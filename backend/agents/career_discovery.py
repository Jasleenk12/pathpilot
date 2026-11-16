import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings
from db.supabase import (
    get_supabase,
    fetch_onet_skills,
    save_career_recommendations,
    log_agent_event,
    SAMPLE_ONET_OCCUPATIONS
)
from agents.state import AgentState

logger = logging.getLogger("pathpilot.agents.career_discovery")


def _heuristic_match_careers(profile: Dict[str, Any], occupations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rule-based career matching fallback."""
    user_skills = set()
    for s in profile.get("skills", []) or profile.get("normalized_skills", []):
        s_name = s.get("skill_name") if isinstance(s, dict) else str(s)
        if s_name:
            user_skills.add(s_name.lower())

    results = []
    preferred = [r.lower() for r in profile.get("preferred_roles", [])]
    
    for occ in occupations[:8]:
        code = occ.get("onet_code")
        title = occ.get("title", "")
        title_lower = title.lower()
        
        # Calculate base score
        score = 75.0
        if any(p in title_lower for p in preferred):
            score += 15.0
            
        matching = []
        missing = []
        
        if "data" in title_lower or "analyst" in title_lower:
            matching = [s for s in ["Python", "SQL", "Statistics"] if any(s.lower() in u for u in user_skills)]
            missing = [s for s in ["Machine Learning", "Data Pipelines", "Tableau"] if not any(s.lower() in u for u in user_skills)]
        elif "software" in title_lower or "developer" in title_lower:
            matching = [s for s in ["JavaScript", "Python", "Git"] if any(s.lower() in u for u in user_skills)]
            missing = [s for s in ["System Design", "Docker", "CI/CD"] if not any(s.lower() in u for u in user_skills)]
        else:
            matching = ["Problem Solving", "Critical Thinking"]
            missing = ["Specialized Domain Knowledge", "Cloud Architecture"]
            
        if not matching:
            matching = ["Analytical Reasoning"]
        if not missing:
            missing = ["Enterprise Systems Design", "Scalability Testing"]
            
        score = min(98.0, max(60.0, score + (len(matching) * 5.0)))
        
        results.append({
            "onet_code": code,
            "title": title,
            "career_title": title,
            "suitability_score": round(score, 1),
            "match_explanation": f"Strong alignment with your technical foundation and analytical interests in {title}.",
            "matching_skills": matching,
            "missing_skills": missing
        })
        
    results.sort(key=lambda x: x["suitability_score"], reverse=True)
    return results[:5]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=False)
def _call_gemini_match(prompt: str) -> Optional[str]:
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


async def discover_careers(state: AgentState) -> AgentState:
    """
    Career Discovery Agent:
    Retrieves O*NET occupational candidates, compares against student profile,
    computes suitability scores, match explanations, and identifies matching/missing skills.
    """
    user_id = state.get("user_id")
    roadmap_id = state.get("roadmap_id")
    session_id = state.get("session_id", "default-session")
    profile = state.get("student_profile", {})
    selected = state.get("selected_career")
    
    await log_agent_event(
        user_id=user_id,
        roadmap_id=roadmap_id,
        session_id=session_id,
        agent_name="Career Discovery",
        status="running",
        message="Fetching O*NET occupations and computing role compatibility...",
        metadata={"step": "fetch_occupations"}
    )
    
    # 1. Fetch O*NET occupations
    client = get_supabase()
    occupations = []
    if client:
        try:
            resp = client.table("onet_occupations").select("onet_code, title, description, job_zone, bright_outlook").limit(30).execute()
            if resp.data:
                occupations = resp.data
        except Exception as e:
            logger.warning(f"Error reading occupations from Supabase: {e}")
            
    if not occupations:
        occupations = SAMPLE_ONET_OCCUPATIONS
        
    # 2. Build Gemini prompt
    occ_summary = [
        {"onet_code": o.get("onet_code"), "title": o.get("title"), "description": o.get("description", "")[:150]}
        for o in occupations[:15]
    ]
    
    prompt = f"""
You are an expert career guidance counselor using the US Department of Labor O*NET framework.
Match this student with the top 5 most suitable careers from the given O*NET occupations:

Student Profile:
{json.dumps(profile, default=str)}

Target Occupations:
{json.dumps(occ_summary, default=str)}

Return a JSON array containing top 5 career recommendations. Each item must be an object with:
- "onet_code": string (matching one of the given codes)
- "title": string
- "suitability_score": float between 0 and 100
- "match_explanation": 2 concise sentences explaining why this role fits the student
- "matching_skills": list of skills the student already possesses for this role
- "missing_skills": list of top 3-4 essential skills the student must acquire
"""
    
    recommendations = []
    try:
        raw_res = _call_gemini_match(prompt)
        if raw_res:
            data = json.loads(raw_res)
            if isinstance(data, list):
                recommendations = data
            elif isinstance(data, dict) and "recommendations" in data:
                recommendations = data["recommendations"]
    except Exception as e:
        logger.warning(f"Gemini career matching failed, falling back to heuristic: {e}")
        
    if not recommendations:
        recommendations = _heuristic_match_careers(profile, occupations)
        
    # Normalize career titles and keys
    for r in recommendations:
        if "career_title" not in r and "title" in r:
            r["career_title"] = r["title"]
            
    # If student previously selected a specific career or onet_code, preserve it
    if selected and selected.get("onet_code"):
        sel_code = selected["onet_code"]
        # mark selected
        for r in recommendations:
            if r.get("onet_code") == sel_code:
                r["is_selected"] = True
                selected = r
                break
    else:
        # Default top match is selected
        if recommendations:
            recommendations[0]["is_selected"] = True
            selected = recommendations[0]

    # Save to database
    if user_id:
        try:
            await save_career_recommendations(user_id, recommendations)
        except Exception as e:
            logger.error(f"Failed to persist career recommendations: {e}")
            
    top_career = selected.get("career_title") or selected.get("title") or "Technology Professional"
    msg = f"Discovered {len(recommendations)} career paths. Top match: {top_career} ({selected.get('suitability_score', 90)}% match)."
    
    await log_agent_event(
        user_id=user_id,
        roadmap_id=roadmap_id,
        session_id=session_id,
        agent_name="Career Discovery",
        status="completed",
        message=msg,
        metadata={"top_career": top_career, "total_matches": len(recommendations)}
    )
    
    events = list(state.get("agent_events", []))
    events.append({
        "agent": "Career Discovery",
        "status": "completed",
        "message": msg,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        **state,
        "career_matches": recommendations,
        "selected_career": selected,
        "agent_events": events
    }
