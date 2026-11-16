"""PathPilot AI — Careers Router"""
import logging
from fastapi import APIRouter, HTTPException, Query, Body
from db.supabase import get_supabase

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/careers/{user_id}/recommendations")
def get_recommendations(user_id: str):
    sb = get_supabase()
    r = sb.table("career_recommendations").select("*").eq("user_id", user_id)\
        .order("suitability_score", desc=True).execute()
    return r.data or []


@router.post("/careers/{user_id}/recommendations/generate")
def generate_recommendations(user_id: str):
    """
    Trigger Career Discovery Agent for a user.
    Returns immediately with job_id; actual generation happens via /roadmap/generate.
    """
    sb = get_supabase()
    # Fetch profile
    profile_r = sb.table("profiles").select("*").eq("id", user_id).maybe_single().execute()
    if not profile_r.data:
        raise HTTPException(404, "Profile not found")

    skills_r = sb.table("student_skills").select("*").eq("user_id", user_id).execute()
    interests_r = sb.table("student_interests").select("*").eq("user_id", user_id).execute()

    profile = profile_r.data
    profile["skills"] = skills_r.data or []
    profile["interests"] = interests_r.data or []

    # Run career discovery synchronously for recommendations-only flow
    from agents.state import AgentState
    from agents.profile_analyzer import analyze_profile
    from agents.career_discovery import discover_careers
    import uuid

    state: AgentState = {
        "user_id": user_id,
        "roadmap_id": None,
        "session_id": str(uuid.uuid4()),
        "student_profile": profile,
        "career_matches": [],
        "selected_career": None,
        "skill_gaps": [],
        "roadmap_stages": [],
        "resources": [],
        "validation_result": {},
        "agent_events": [],
        "error": None,
        "retry_count": 0,
    }
    state = analyze_profile(state)
    state = discover_careers(state)

    return {"career_matches": state.get("career_matches", []), "status": "complete"}


@router.post("/careers/{user_id}/select")
def select_career(user_id: str, data: dict = Body(...)):
    """Mark a career as selected for the user."""
    onet_code = data.get("onet_code")
    recommendation_id = data.get("recommendation_id")
    if not onet_code:
        raise HTTPException(400, "onet_code required")

    sb = get_supabase()
    # Deselect all
    sb.table("career_recommendations").update({"is_selected": False}).eq("user_id", user_id).execute()
    # Select the chosen one
    if recommendation_id:
        sb.table("career_recommendations").update({"is_selected": True})\
            .eq("id", recommendation_id).eq("user_id", user_id).execute()
    else:
        sb.table("career_recommendations").update({"is_selected": True})\
            .eq("onet_code", onet_code).eq("user_id", user_id).execute()

    return {"selected": True, "onet_code": onet_code}


@router.get("/careers/compare")
def compare_careers(codes: str = Query(..., description="Comma-separated O*NET codes")):
    """Side-by-side comparison of 2-3 O*NET occupations."""
    code_list = [c.strip() for c in codes.split(",")][:3]
    sb = get_supabase()
    result = {}
    for code in code_list:
        occ = sb.table("onet_occupations").select("*").eq("onet_code", code).maybe_single().execute()
        skills = sb.table("onet_skills").select("*").eq("onet_code", code)\
            .order("importance", desc=True).limit(10).execute()
        tech = sb.table("onet_technology").select("*").eq("onet_code", code).limit(10).execute()
        result[code] = {
            "occupation": occ.data or {},
            "top_skills": skills.data or [],
            "technology": tech.data or [],
        }
    return result
