import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings
from db.supabase import log_agent_event
from agents.state import AgentState

logger = logging.getLogger("pathpilot.agents.profile_analyzer")


def _get_mock_analysis(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback profile analysis when Gemini API is unavailable."""
    skills = profile.get("skills", [])
    interests = profile.get("interests", [])
    edu_level = profile.get("education_level", "bachelor")
    
    # Calculate experience level (1-5)
    exp_level = 2
    if edu_level in ["master", "phd"]:
        exp_level = 4
    elif edu_level == "bachelor":
        exp_level = 3
    elif skills and len(skills) > 4:
        exp_level = 3
        
    # Infer Holland RIASEC codes
    riasec = ["Investigative", "Realistic"]
    interest_names = [i.get("interest", "") if isinstance(i, dict) else str(i) for i in interests]
    interest_str = " ".join(interest_names).lower()
    
    if any(k in interest_str for k in ["design", "creative", "ui", "ux", "art"]):
        riasec.append("Artistic")
    elif any(k in interest_str for k in ["business", "startup", "management", "leadership"]):
        riasec.append("Enterprising")
    else:
        riasec.append("Conventional")
        
    skill_names = [s.get("skill_name", "") if isinstance(s, dict) else str(s) for s in skills]
    skills_text = ", ".join(skill_names[:3]) if skill_names else "core computing"
    
    summary = (
        f"Goal-oriented learner with developing proficiency in {skills_text} and strong technical curiosity. "
        f"Aims to bridge theoretical knowledge into practical, production-ready engineering and problem solving."
    )
    
    normalized_skills = []
    for s in skills:
        s_name = s.get("skill_name") if isinstance(s, dict) else str(s)
        s_prof = s.get("proficiency_level", 2) if isinstance(s, dict) else 2
        normalized_skills.append({
            "skill_name": s_name,
            "category": "technical",
            "proficiency_level": s_prof
        })
        
    return {
        "normalized_skills": normalized_skills,
        "riasec_codes": riasec[:3],
        "experience_level": exp_level,
        "summary": summary
    }


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=False
)
def _call_gemini_structured(prompt: str) -> Optional[str]:
    """Call Gemini 1.5 Flash with retry."""
    settings = get_settings()
    key = settings.gemini_api_key.strip()
    if not key or "your_gemini" in key:
        return None
        
    import google.generativeai as genai
    genai.configure(api_key=key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={"response_mime_type": "application/json"}
    )
    response = model.generate_content(prompt)
    return response.text if response else None


async def analyze_profile(state: AgentState) -> AgentState:
    """
    Profile Analyzer Agent:
    Enriches student profile with normalized skills, Holland RIASEC codes,
    experience level, and a concise 2-sentence summary.
    """
    user_id = state.get("user_id")
    roadmap_id = state.get("roadmap_id")
    session_id = state.get("session_id", "default-session")
    profile = state.get("student_profile", {})
    
    # Log start event
    await log_agent_event(
        user_id=user_id,
        roadmap_id=roadmap_id,
        session_id=session_id,
        agent_name="Profile Analyzer",
        status="running",
        message="Analyzing student background, academic history, and skills...",
        metadata={"step": "profile_analysis_started"}
    )
    
    prompt = f"""
You are an expert career counselor and skills taxonomist. Analyze this student profile:
Profile Data: {json.dumps(profile, default=str)}

Respond with a JSON object containing:
1. "normalized_skills": List of objects with keys "skill_name" (standardized title), "category" ('technical'|'soft'|'tool'|'domain'), and "proficiency_level" (integer 1-5).
2. "riasec_codes": List of top 3 Holland RIASEC codes ('Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional') that match their interests and background.
3. "experience_level": Integer from 1 (Novice) to 5 (Senior/Advanced).
4. "summary": Exactly 2 sentences summarizing the student's foundation and learning trajectory.
"""
    
    analysis_data = None
    try:
        raw_resp = _call_gemini_structured(prompt)
        if raw_resp:
            analysis_data = json.loads(raw_resp)
    except Exception as e:
        logger.warning(f"Gemini call failed in Profile Analyzer, falling back to heuristic: {e}")
        
    if not analysis_data or not isinstance(analysis_data, dict):
        analysis_data = _get_mock_analysis(profile)
        
    # Enrich profile in state
    enriched_profile = {
        **profile,
        "riasec_codes": analysis_data.get("riasec_codes", ["Investigative", "Realistic", "Conventional"]),
        "experience_level": analysis_data.get("experience_level", 2),
        "profile_summary": analysis_data.get("summary", ""),
        "normalized_skills": analysis_data.get("normalized_skills", profile.get("skills", []))
    }
    
    exp_lvl = enriched_profile["experience_level"]
    top_interests = ", ".join(enriched_profile["riasec_codes"][:2])
    msg = f"Profile analyzed. Experience level: {exp_lvl}/5. Top Holland types: {top_interests}."
    
    event_data = {
        "agent": "Profile Analyzer",
        "status": "completed",
        "message": msg,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await log_agent_event(
        user_id=user_id,
        roadmap_id=roadmap_id,
        session_id=session_id,
        agent_name="Profile Analyzer",
        status="completed",
        message=msg,
        metadata={"experience_level": exp_lvl, "riasec": enriched_profile["riasec_codes"]}
    )
    
    events = list(state.get("agent_events", []))
    events.append(event_data)
    
    return {
        **state,
        "student_profile": enriched_profile,
        "agent_events": events
    }
