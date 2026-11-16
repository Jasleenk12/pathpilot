import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings
from db.supabase import fetch_onet_skills, save_skill_gap, log_agent_event
from agents.state import AgentState

logger = logging.getLogger("pathpilot.agents.skill_gap")


def _heuristic_skill_gap(student_skills: List[Dict[str, Any]], required_skills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rule-based skill gap categorization."""
    user_skill_map = {}
    for s in student_skills:
        name = s.get("skill_name") if isinstance(s, dict) else str(s)
        level = s.get("proficiency_level", 1) if isinstance(s, dict) else 1
        if name:
            user_skill_map[name.lower()] = float(level)
            
    gaps = []
    for idx, r in enumerate(required_skills):
        r_name = r.get("skill_name", "Skill")
        r_importance = float(r.get("importance", 80.0))
        # O*NET level is 0-7, normalize to 1-5 scale
        r_raw_level = float(r.get("level", 4.5))
        r_level_norm = min(5.0, max(1.0, round((r_raw_level / 7.0) * 5.0, 1)))
        
        # Check if student has skill
        user_level = 0.0
        for u_name, u_lvl in user_skill_map.items():
            if u_name in r_name.lower() or r_name.lower() in u_name:
                user_level = max(user_level, u_lvl)
                
        if user_level >= r_level_norm:
            cat = "acquired"
        elif user_level > 0.0:
            cat = "needs_improvement"
        else:
            cat = "must_learn"
            
        gaps.append({
            "skill_name": r_name,
            "student_level": user_level,
            "required_level": r_level_norm,
            "gap_category": cat,
            "onet_importance": r_importance,
            "priority": idx + 1
        })
        
    gaps.sort(key=lambda x: x["onet_importance"], reverse=True)
    for i, g in enumerate(gaps):
        g["priority"] = i + 1
    return gaps


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=False)
def _call_gemini_gap(prompt: str) -> Optional[str]:
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
    resp = model.generate_content(prompt)
    return resp.text if resp else None


async def analyze_skill_gap(state: AgentState) -> AgentState:
    """
    Skill Gap Analysis Agent:
    Evaluates student's current proficiency against O*NET occupational standards,
    categorizing each requirement as 'acquired', 'needs_improvement', or 'must_learn'.
    """
    user_id = state.get("user_id")
    roadmap_id = state.get("roadmap_id")
    session_id = state.get("session_id", "default-session")
    profile = state.get("student_profile", {})
    selected = state.get("selected_career") or {}
    
    onet_code = selected.get("onet_code") or "15-2051.00"
    career_title = selected.get("career_title") or selected.get("title") or "Selected Career"
    
    await log_agent_event(
        user_id=user_id,
        roadmap_id=roadmap_id,
        session_id=session_id,
        agent_name="Skill Gap Analyzer",
        status="running",
        message=f"Benchmarking current competencies against {career_title} standards...",
        metadata={"onet_code": onet_code}
    )
    
    # 1. Fetch O*NET skills
    required_skills = await fetch_onet_skills(onet_code)
    student_skills = profile.get("skills", []) or profile.get("normalized_skills", [])
    
    prompt = f"""
Compare this student's skills against the industry benchmark requirements for {career_title} (O*NET {onet_code}):

Student Skills:
{json.dumps(student_skills, default=str)}

Required O*NET Competencies:
{json.dumps(required_skills, default=str)}

For each required competency, output a JSON array of objects with:
- "skill_name": string
- "student_level": float (0.0 to 5.0)
- "required_level": float (1.0 to 5.0)
- "gap_category": one of ["acquired", "needs_improvement", "must_learn"]
- "onet_importance": float (0 to 100)
- "priority": integer
"""
    
    gap_items = []
    try:
        raw_res = _call_gemini_gap(prompt)
        if raw_res:
            data = json.loads(raw_res)
            if isinstance(data, list):
                gap_items = data
            elif isinstance(data, dict) and "skills" in data:
                gap_items = data["skills"]
    except Exception as e:
        logger.warning(f"Gemini skill gap call failed, using heuristic: {e}")
        
    if not gap_items:
        gap_items = _heuristic_skill_gap(student_skills, required_skills)
        
    # Sort by importance
    gap_items.sort(key=lambda x: float(x.get("onet_importance", 0.0)), reverse=True)
    for idx, item in enumerate(gap_items):
        item["priority"] = idx + 1
        
    # Persist in DB
    if user_id:
        try:
            await save_skill_gap(user_id=user_id, roadmap_id=roadmap_id, gaps=gap_items, onet_code=onet_code)
        except Exception as e:
            logger.error(f"Error saving skill gaps: {e}")
            
    must_learn_count = sum(1 for g in gap_items if g.get("gap_category") == "must_learn")
    improve_count = sum(1 for g in gap_items if g.get("gap_category") == "needs_improvement")
    acquired_count = sum(1 for g in gap_items if g.get("gap_category") == "acquired")
    
    msg = f"Identified {must_learn_count} skills to learn, {improve_count} to sharpen, and {acquired_count} verified."
    
    await log_agent_event(
        user_id=user_id,
        roadmap_id=roadmap_id,
        session_id=session_id,
        agent_name="Skill Gap Analyzer",
        status="completed",
        message=msg,
        metadata={"must_learn": must_learn_count, "needs_improvement": improve_count, "acquired": acquired_count}
    )
    
    events = list(state.get("agent_events", []))
    events.append({
        "agent": "Skill Gap Analyzer",
        "status": "completed",
        "message": msg,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        **state,
        "skill_gaps": gap_items,
        "agent_events": events
    }
