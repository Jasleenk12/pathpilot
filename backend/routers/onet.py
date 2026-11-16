"""PathPilot AI — O*NET Explorer Router"""
from fastapi import APIRouter, Query
from db.supabase import get_supabase

router = APIRouter()


@router.get("/onet/search")
def search_onet(q: str = Query("", min_length=0)):
    """Full-text search across O*NET occupations."""
    sb = get_supabase()
    if not q.strip():
        # Return all with limit
        r = sb.table("onet_occupations").select("*").limit(20).execute()
    else:
        # Use ilike for simple search (pg_trgm not guaranteed in all Supabase configs)
        r = sb.table("onet_occupations").select("*")\
            .ilike("title", f"%{q}%").limit(20).execute()
    return r.data or []


@router.get("/onet/occupation/{onet_code}")
def get_occupation(onet_code: str):
    sb = get_supabase()
    occ_r = sb.table("onet_occupations").select("*").eq("onet_code", onet_code).maybe_single().execute()
    if not occ_r.data:
        from fastapi import HTTPException
        raise HTTPException(404, "Occupation not found")
    occ = occ_r.data

    skills_r = sb.table("onet_skills").select("*").eq("onet_code", onet_code)\
        .order("importance", desc=True).limit(15).execute()
    tech_r = sb.table("onet_technology").select("*").eq("onet_code", onet_code).limit(15).execute()
    activities_r = sb.table("onet_work_activities").select("*").eq("onet_code", onet_code)\
        .order("importance", desc=True).limit(10).execute()
    interests_r = sb.table("onet_interests").select("*").eq("onet_code", onet_code).execute()

    return {
        **occ,
        "skills": skills_r.data or [],
        "technology": tech_r.data or [],
        "work_activities": activities_r.data or [],
        "interests": interests_r.data or [],
    }


@router.get("/onet/skills/{onet_code}")
def get_onet_skills(onet_code: str):
    sb = get_supabase()
    r = sb.table("onet_skills").select("*").eq("onet_code", onet_code)\
        .order("importance", desc=True).execute()
    return r.data or []


@router.get("/onet/technology/{onet_code}")
def get_onet_technology(onet_code: str):
    sb = get_supabase()
    r = sb.table("onet_technology").select("*").eq("onet_code", onet_code).execute()
    return r.data or []


@router.get("/onet/trending")
def get_trending():
    """Return bright outlook occupations."""
    sb = get_supabase()
    r = sb.table("onet_occupations").select("*").eq("bright_outlook", True)\
        .order("median_annual_wage", desc=True).limit(12).execute()
    return r.data or []
