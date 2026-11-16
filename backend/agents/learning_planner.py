"""
PathPilot AI — Learning Path Planner Agent
Agent 4: Creates sequential learning stages from skill gaps.
"""
import json
import logging
from datetime import datetime
from typing import Any

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from agents.state import AgentState
from config import get_settings
from db.supabase import log_agent_event

logger = logging.getLogger(__name__)
settings = get_settings()

AGENT_NAME = "Learning Planner"


def _mock_stages(skill_gaps: list[dict], weekly_hours: int, duration_months: int) -> list[dict]:
    """Return mock stages when Gemini is unavailable."""
    must_learn = [g["skill_name"] for g in skill_gaps if g.get("gap_category") == "must_learn"][:6]
    needs_improvement = [g["skill_name"] for g in skill_gaps if g.get("gap_category") == "needs_improvement"][:4]
    all_skills = must_learn + needs_improvement

    stages = []
    skills_per_stage = max(2, len(all_skills) // 5)
    for i, chunk_start in enumerate(range(0, len(all_skills), skills_per_stage)):
        chunk = all_skills[chunk_start: chunk_start + skills_per_stage]
        stages.append({
            "stage_number": i + 1,
            "stage_title": f"Stage {i + 1}: {', '.join(chunk[:2])}",
            "stage_description": f"Focus on learning {', '.join(chunk)} through hands-on practice.",
            "skills_to_learn": chunk,
            "prerequisites": [] if i == 0 else [all_skills[chunk_start - 1]],
            "duration_weeks": max(2, (duration_months * 4) // max(1, (len(all_skills) // skills_per_stage + 1))),
        })
    return stages[:8]  # max 8 stages


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def _call_gemini_planner(prompt: str) -> str:
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text


def plan_learning_path(state: AgentState) -> AgentState:
    """Create sequential learning stages from skill gaps."""
    user_id = state["user_id"]
    session_id = state["session_id"]
    roadmap_id = state.get("roadmap_id")
    skill_gaps = state.get("skill_gaps", [])
    profile = state.get("student_profile", {})
    weekly_hours = profile.get("weekly_hours", 10)
    duration_months = profile.get("roadmap_duration_months", 12)
    selected_career = state.get("selected_career", {})
    corrections = state.get("validation_result", {}).get("corrections", [])

    log_agent_event(
        user_id, roadmap_id, session_id, AGENT_NAME, "started",
        f"Planning {duration_months}-month roadmap for {selected_career.get('title', 'target career')} "
        f"({weekly_hours}h/week)..."
    )

    if not settings.gemini_api_key:
        stages = _mock_stages(skill_gaps, weekly_hours, duration_months)
        log_agent_event(user_id, roadmap_id, session_id, AGENT_NAME, "completed",
                        f"Created {len(stages)} learning stages (demo mode).")
        return {**state, "roadmap_stages": stages}

    must_learn = [g for g in skill_gaps if g.get("gap_category") == "must_learn"]
    needs_improvement = [g for g in skill_gaps if g.get("gap_category") == "needs_improvement"]

    correction_text = ""
    if corrections:
        correction_text = f"\n\nIMPORTANT CORRECTIONS FROM PREVIOUS ATTEMPT:\n" + "\n".join(f"- {c}" for c in corrections)

    prompt = f"""You are a career learning path designer. Create a detailed, sequential learning roadmap.

TARGET CAREER: {selected_career.get('title', 'Unknown')} (O*NET: {selected_career.get('onet_code', '')})

STUDENT CONTEXT:
- Education: {profile.get('education_level', 'bachelor')} in {profile.get('specialization', 'unknown')}
- Weekly available hours: {weekly_hours}h/week
- Desired roadmap duration: {duration_months} months
- Experience level: {profile.get('experience_level', 2)}/5

SKILLS TO LEARN (Must Learn - Critical):
{json.dumps([{{'skill': g['skill_name'], 'importance': g.get('onet_importance', 50)}} for g in must_learn[:10]], indent=2)}

SKILLS TO IMPROVE (Needs Improvement):
{json.dumps([{{'skill': g['skill_name'], 'importance': g.get('onet_importance', 50)}} for g in needs_improvement[:6]], indent=2)}
{correction_text}

INSTRUCTIONS:
1. Create 5-9 learning STAGES that are sequential (each builds on the previous)
2. Stage 1 should cover fundamentals/prerequisites, later stages advanced topics
3. Each stage duration must be realistic for {weekly_hours}h/week availability
4. Total duration should be approximately {duration_months} months
5. Order skills logically: basics → intermediate → advanced → specialized
6. Include BOTH "must learn" and "needs improvement" skills across stages

Return ONLY valid JSON (no markdown, no explanation):
{{
  "stages": [
    {{
      "stage_number": 1,
      "stage_title": "Short descriptive title",
      "stage_description": "2-3 sentence description of what will be learned and why",
      "skills_to_learn": ["skill1", "skill2"],
      "prerequisites": [],
      "duration_weeks": 4
    }}
  ]
}}"""

    try:
        raw = _call_gemini_planner(prompt)
        # Strip markdown fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip().rstrip("```").strip()

        data = json.loads(raw)
        stages = data.get("stages", [])

        # Validate and normalize
        for i, stage in enumerate(stages):
            stage["stage_number"] = i + 1
            if not isinstance(stage.get("skills_to_learn"), list):
                stage["skills_to_learn"] = []
            if not isinstance(stage.get("prerequisites"), list):
                stage["prerequisites"] = []
            if not isinstance(stage.get("duration_weeks"), int):
                stage["duration_weeks"] = 4

        log_agent_event(
            user_id, roadmap_id, session_id, AGENT_NAME, "completed",
            f"Created {len(stages)} learning stages spanning ~{sum(s.get('duration_weeks', 4) for s in stages) // 4} months."
        )
        return {**state, "roadmap_stages": stages}

    except Exception as e:
        logger.error(f"Learning planner error: {e}")
        stages = _mock_stages(skill_gaps, weekly_hours, duration_months)
        log_agent_event(user_id, roadmap_id, session_id, AGENT_NAME, "completed",
                        f"Created {len(stages)} learning stages (fallback).")
        return {**state, "roadmap_stages": stages}
