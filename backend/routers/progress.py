"""PathPilot AI — Progress Tracker Router"""
from fastapi import APIRouter, HTTPException
from db.supabase import get_supabase

router = APIRouter()


@router.get("/progress/{user_id}")
def get_progress(user_id: str):
    sb = get_supabase()

    # Get primary roadmap
    rm_r = sb.table("roadmaps").select("*").eq("user_id", user_id)\
        .eq("is_primary", True).maybe_single().execute()
    roadmap = rm_r.data or {}

    if not roadmap:
        return {
            "roadmap_completion": 0, "skills_acquired": 0,
            "courses_completed": 0, "projects_completed": 0,
            "milestones_achieved": 0, "current_stage": 0, "total_stages": 0,
        }

    roadmap_id = roadmap["id"]
    stages_r = sb.table("roadmap_stages").select("*").eq("roadmap_id", roadmap_id).execute()
    stages = stages_r.data or []

    courses_done = 0
    projects_done = 0
    for stage in stages:
        tasks_r = sb.table("roadmap_tasks").select("task_type,is_completed")\
            .eq("stage_id", stage["id"]).execute()
        for t in (tasks_r.data or []):
            if t["is_completed"]:
                if t["task_type"] == "course":
                    courses_done += 1
                elif t["task_type"] == "project":
                    projects_done += 1

    # Skills acquired = student skills with proficiency >= 3
    skills_r = sb.table("student_skills").select("proficiency_level")\
        .eq("user_id", user_id).gte("proficiency_level", 3).execute()

    milestones_r = sb.table("milestones").select("is_achieved")\
        .eq("roadmap_id", roadmap_id).eq("is_achieved", True).execute()

    completed_stages = sum(1 for s in stages if s.get("status") == "completed")
    current_stage = completed_stages + 1

    return {
        "roadmap_completion": roadmap.get("completion_percentage", 0),
        "skills_acquired": len(skills_r.data or []),
        "courses_completed": courses_done,
        "projects_completed": projects_done,
        "milestones_achieved": len(milestones_r.data or []),
        "current_stage": min(current_stage, len(stages)),
        "total_stages": len(stages),
        "stages": stages,
    }


@router.get("/progress/{user_id}/roadmap/{roadmap_id}")
def get_roadmap_progress(user_id: str, roadmap_id: str):
    sb = get_supabase()
    stages_r = sb.table("roadmap_stages").select("*")\
        .eq("roadmap_id", roadmap_id).order("stage_number").execute()
    stages = stages_r.data or []
    for stage in stages:
        tasks_r = sb.table("roadmap_tasks").select("*")\
            .eq("stage_id", stage["id"]).execute()
        stage["tasks"] = tasks_r.data or []
    return {"stages": stages, "roadmap_id": roadmap_id}


@router.post("/progress/{user_id}/milestones/{milestone_id}/achieve")
def achieve_milestone(user_id: str, milestone_id: str):
    sb = get_supabase()
    from datetime import datetime
    sb.table("milestones").update({
        "is_achieved": True,
        "achieved_at": datetime.utcnow().isoformat(),
    }).eq("id", milestone_id).execute()
    return {"achieved": True}


@router.get("/progress/{user_id}/timeline")
def get_timeline(user_id: str):
    """Recent activity: completed tasks."""
    sb = get_supabase()
    rm_r = sb.table("roadmaps").select("id").eq("user_id", user_id)\
        .eq("is_primary", True).maybe_single().execute()
    if not rm_r.data:
        return []

    roadmap_id = rm_r.data["id"]
    stages_r = sb.table("roadmap_stages").select("id,stage_title").eq("roadmap_id", roadmap_id).execute()
    stage_map = {s["id"]: s["stage_title"] for s in (stages_r.data or [])}

    tasks_r = sb.table("roadmap_tasks").select("*")\
        .in_("stage_id", list(stage_map.keys()))\
        .eq("is_completed", True)\
        .order("completed_at", desc=True).limit(20).execute()

    result = []
    for t in (tasks_r.data or []):
        result.append({
            "task_title": t["title"],
            "task_type": t["task_type"],
            "stage_title": stage_map.get(t["stage_id"], ""),
            "completed_at": t.get("completed_at", ""),
        })
    return result
