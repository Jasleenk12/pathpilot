"""PathPilot AI — Profile Router"""
import logging
from fastapi import APIRouter, HTTPException, Body
from db.supabase import get_supabase

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/profile/{user_id}")
def get_profile(user_id: str):
    sb = get_supabase()
    r = sb.table("profiles").select("*").eq("id", user_id).maybe_single().execute()
    if not r.data:
        raise HTTPException(404, "Profile not found")
    return r.data


@router.post("/profile", status_code=201)
def create_profile(data: dict = Body(...)):
    sb = get_supabase()
    r = sb.table("profiles").insert(data).execute()
    return r.data[0] if r.data else {}


@router.put("/profile/{user_id}")
def update_profile(user_id: str, data: dict = Body(...)):
    sb = get_supabase()
    data.pop("id", None)
    r = sb.table("profiles").update(data).eq("id", user_id).execute()
    return r.data[0] if r.data else {}


@router.get("/profile/{user_id}/skills")
def get_skills(user_id: str):
    sb = get_supabase()
    r = sb.table("student_skills").select("*").eq("user_id", user_id).execute()
    return r.data or []


@router.post("/profile/{user_id}/skills", status_code=201)
def add_skill(user_id: str, data: dict = Body(...)):
    sb = get_supabase()
    data["user_id"] = user_id
    r = sb.table("student_skills").insert(data).execute()
    return r.data[0] if r.data else {}


@router.delete("/profile/{user_id}/skills/{skill_id}")
def delete_skill(user_id: str, skill_id: str):
    sb = get_supabase()
    sb.table("student_skills").delete().eq("id", skill_id).eq("user_id", user_id).execute()
    return {"deleted": True}


@router.get("/profile/{user_id}/experience")
def get_experience(user_id: str):
    sb = get_supabase()
    r = sb.table("student_experience").select("*").eq("user_id", user_id).execute()
    return r.data or []


@router.post("/profile/{user_id}/experience", status_code=201)
def add_experience(user_id: str, data: dict = Body(...)):
    sb = get_supabase()
    data["user_id"] = user_id
    r = sb.table("student_experience").insert(data).execute()
    return r.data[0] if r.data else {}


@router.put("/profile/{user_id}/onboarding")
def complete_onboarding(user_id: str, data: dict = Body(...)):
    """Accept full onboarding payload and persist all sub-entities."""
    sb = get_supabase()

    # Update core profile
    profile_fields = {k: v for k, v in data.items()
                      if k in ("full_name", "degree", "specialization", "education_level",
                               "graduation_year", "university", "weekly_hours",
                               "roadmap_duration_months", "preferred_roles", "career_goals")}
    profile_fields["onboarding_completed"] = True
    sb.table("profiles").update(profile_fields).eq("id", user_id).execute()

    # Upsert skills
    if data.get("skills"):
        # Remove existing
        sb.table("student_skills").delete().eq("user_id", user_id).execute()
        skill_rows = [
            {"user_id": user_id, "skill_name": s["skill_name"],
             "skill_category": s.get("skill_category", "technical"),
             "proficiency_level": s.get("proficiency_level", 3)}
            for s in data["skills"]
        ]
        if skill_rows:
            sb.table("student_skills").insert(skill_rows).execute()

    # Upsert soft skills
    if data.get("soft_skills"):
        rows = [{"user_id": user_id, "skill_name": s, "skill_category": "soft", "proficiency_level": 3}
                for s in data["soft_skills"]]
        if rows:
            sb.table("student_skills").insert(rows).execute()

    # Upsert interests
    if data.get("interests"):
        sb.table("student_interests").delete().eq("user_id", user_id).execute()
        int_rows = [{"user_id": user_id, "interest": i, "interest_type": "domain"}
                    for i in data["interests"]]
        if int_rows:
            sb.table("student_interests").insert(int_rows).execute()

    # Upsert experience
    if data.get("experience"):
        sb.table("student_experience").delete().eq("user_id", user_id).execute()
        exp_rows = [{"user_id": user_id, **e} for e in data["experience"]]
        if exp_rows:
            sb.table("student_experience").insert(exp_rows).execute()

    return {"success": True, "onboarding_completed": True}
