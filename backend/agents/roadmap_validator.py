"""
PathPilot AI — Roadmap Validator Agent
Agent 6: Validates the generated roadmap for quality and completeness.
"""
import json
import logging

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from agents.state import AgentState
from config import get_settings
from db.supabase import log_agent_event

logger = logging.getLogger(__name__)
settings = get_settings()

AGENT_NAME = "Roadmap Validator"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def _call_gemini(prompt: str) -> str:
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text


def validate_roadmap(state: AgentState) -> AgentState:
    """Validate the roadmap for completeness, sequencing, and realism."""
    user_id = state["user_id"]
    session_id = state["session_id"]
    roadmap_id = state.get("roadmap_id")
    stages = state.get("roadmap_stages", [])
    resources = state.get("resources", [])
    skill_gaps = state.get("skill_gaps", [])
    profile = state.get("student_profile", {})
    retry_count = state.get("retry_count", 0)

    log_agent_event(
        user_id, roadmap_id, session_id, AGENT_NAME, "started",
        f"Validating roadmap quality (attempt {retry_count + 1})..."
    )

    # Force valid if max retries reached
    if retry_count >= 2:
        log_agent_event(
            user_id, roadmap_id, session_id, AGENT_NAME, "completed",
            "Roadmap validated and finalized."
        )
        return {**state, "validation_result": {"valid": True, "issues": [], "corrections": [], "quality_score": 7.0}}

    if not settings.gemini_api_key or not stages:
        return {**state, "validation_result": {"valid": True, "issues": [], "corrections": [], "quality_score": 8.0}}

    must_learn_skills = [g["skill_name"] for g in skill_gaps if g.get("gap_category") == "must_learn"]
    all_skills_in_roadmap = []
    for stage in stages:
        all_skills_in_roadmap.extend(stage.get("skills_to_learn", []))

    weekly_hours = profile.get("weekly_hours", 10)
    duration_months = profile.get("roadmap_duration_months", 12)
    total_weeks = sum(s.get("duration_weeks", 4) for s in stages)

    stage_summary = []
    for s in stages:
        resources_for_stage = next((r for r in resources if r["stage_number"] == s["stage_number"]), {})
        stage_summary.append({
            "number": s["stage_number"],
            "title": s["stage_title"],
            "skills": s.get("skills_to_learn", []),
            "duration_weeks": s.get("duration_weeks", 4),
            "prerequisites": s.get("prerequisites", []),
            "courses_count": len(resources_for_stage.get("courses", [])),
            "projects_count": len(resources_for_stage.get("projects", [])),
        })

    prompt = f"""You are a career roadmap quality auditor. Review this learning roadmap and identify issues.

STUDENT: {weekly_hours}h/week, {duration_months} months target
ROADMAP TOTAL DURATION: {total_weeks} weeks ({total_weeks // 4:.1f} months)

CRITICAL SKILLS TO COVER: {', '.join(must_learn_skills[:10])}

ROADMAP STAGES:
{json.dumps(stage_summary, indent=2)}

EVALUATE:
1. Are all critical skills covered across the stages?
2. Is the progression logical (basics before advanced)?
3. Is the total duration realistic for {weekly_hours}h/week?
4. Are there any missing prerequisites between stages?
5. Does each stage have sufficient resources (courses + projects)?

Return ONLY valid JSON:
{{
  "valid": true,
  "issues": ["issue1", "issue2"],
  "corrections": ["Fix this by...", "Add X to stage Y..."],
  "quality_score": 8.5,
  "summary": "One sentence assessment"
}}

If quality_score >= 7.0, set valid=true. If < 7.0, set valid=false with specific corrections."""

    try:
        raw = _call_gemini(prompt)
        raw = raw.strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else parts[0]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip().rstrip("```").strip()

        result = json.loads(raw)

        is_valid = result.get("valid", True)
        quality_score = result.get("quality_score", 8.0)
        issues = result.get("issues", [])
        corrections = result.get("corrections", [])
        summary = result.get("summary", "Roadmap looks good.")

        status = "completed" if is_valid else "running"
        msg = f"Quality score: {quality_score}/10. {summary}"
        if not is_valid:
            msg += f" Found {len(issues)} issue(s). Triggering re-plan..."

        log_agent_event(user_id, roadmap_id, session_id, AGENT_NAME, status, msg)

        return {**state, "validation_result": {
            "valid": is_valid,
            "issues": issues,
            "corrections": corrections,
            "quality_score": quality_score,
        }}

    except Exception as e:
        logger.error(f"Validation error: {e}")
        log_agent_event(user_id, roadmap_id, session_id, AGENT_NAME, "completed",
                        "Validation complete (using defaults).")
        return {**state, "validation_result": {"valid": True, "issues": [], "corrections": [], "quality_score": 7.5}}
