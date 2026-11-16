"""PathPilot AI — Roadmap Router with SSE streaming"""
import asyncio
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Body, BackgroundTasks
from fastapi.responses import StreamingResponse
from db.supabase import get_supabase

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _build_profile_for_agent(user_id: str, sb) -> dict:
    profile_r = sb.table("profiles").select("*").eq("id", user_id).maybe_single().execute()
    skills_r = sb.table("student_skills").select("*").eq("user_id", user_id).execute()
    interests_r = sb.table("student_interests").select("*").eq("user_id", user_id).execute()
    exp_r = sb.table("student_experience").select("*").eq("user_id", user_id).execute()
    profile = profile_r.data or {}
    profile["skills"] = skills_r.data or []
    profile["interests"] = interests_r.data or []
    profile["experience"] = exp_r.data or []
    return profile


def _persist_roadmap(sb, user_id: str, final_state: dict, roadmap_id: str, career: dict):
    """Write all generated roadmap data to Supabase."""
    stages = final_state.get("roadmap_stages", [])
    resources = final_state.get("resources", [])

    # Update roadmap status
    sb.table("roadmaps").update({"status": "active"}).eq("id", roadmap_id).execute()

    # Persist stages and tasks
    for stage_data in stages:
        stage_num = stage_data["stage_number"]
        stage_r = sb.table("roadmap_stages").insert({
            "roadmap_id": roadmap_id,
            "stage_number": stage_num,
            "stage_title": stage_data.get("stage_title", f"Stage {stage_num}"),
            "stage_description": stage_data.get("stage_description", ""),
            "skills_to_learn": stage_data.get("skills_to_learn", []),
            "prerequisites": stage_data.get("prerequisites", []),
            "duration_weeks": stage_data.get("duration_weeks", 4),
            "status": "locked" if stage_num > 1 else "in_progress",
        }).execute()

        if not stage_r.data:
            continue
        stage_id = stage_r.data[0]["id"]

        # Find resources for this stage
        stage_resources = next((r for r in resources if r["stage_number"] == stage_num), {})
        order = 0
        for course in stage_resources.get("courses", []):
            sb.table("roadmap_tasks").insert({
                "stage_id": stage_id,
                "task_type": "course",
                "title": course.get("title", ""),
                "description": course.get("description", ""),
                "platform": course.get("platform", ""),
                "url": course.get("url_hint", ""),
                "duration_hours": course.get("duration_hours", 10),
                "difficulty": course.get("difficulty", "intermediate"),
                "skills_covered": course.get("skills_covered", []),
                "source": "ai_recommended",
                "display_order": order,
            }).execute()
            order += 1

        for project in stage_resources.get("projects", []):
            sb.table("roadmap_tasks").insert({
                "stage_id": stage_id,
                "task_type": "project",
                "title": project.get("title", ""),
                "description": project.get("description", ""),
                "duration_hours": project.get("estimated_hours", 10),
                "skills_covered": project.get("skills_covered", []),
                "source": "ai_recommended",
                "display_order": order,
            }).execute()
            order += 1

        for cert in stage_resources.get("certifications", []):
            sb.table("roadmap_tasks").insert({
                "stage_id": stage_id,
                "task_type": "certification",
                "title": cert.get("name", ""),
                "platform": cert.get("provider", ""),
                "url": cert.get("url_hint", ""),
                "source": "ai_recommended",
                "display_order": order,
            }).execute()
            order += 1

    # Persist skill gap if present
    skill_gaps = final_state.get("skill_gaps", [])
    if skill_gaps:
        analysis_r = sb.table("skill_gap_analyses").insert({
            "user_id": user_id,
            "roadmap_id": roadmap_id,
            "onet_code": career.get("onet_code", ""),
        }).execute()
        if analysis_r.data:
            analysis_id = analysis_r.data[0]["id"]
            gap_rows = [
                {
                    "analysis_id": analysis_id,
                    "skill_name": g.get("skill_name", ""),
                    "student_level": g.get("student_level", 0),
                    "required_level": g.get("required_level", 5),
                    "gap_category": g.get("gap_category", "must_learn"),
                    "onet_importance": g.get("onet_importance", 50),
                    "priority": g.get("priority", 5),
                }
                for g in skill_gaps
            ]
            if gap_rows:
                sb.table("skill_gap_items").insert(gap_rows).execute()


async def _run_workflow_background(user_id: str, roadmap_id: str, career: dict, profile: dict):
    """Background coroutine running the full LangGraph pipeline."""
    from agents.graph import run_roadmap_workflow
    sb = get_supabase()
    try:
        final_state = await run_roadmap_workflow(
            user_id=user_id,
            student_profile=profile,
            selected_career=career,
            roadmap_id=roadmap_id,
        )
        _persist_roadmap(sb, user_id, final_state, roadmap_id, career)
    except Exception as e:
        logger.error(f"Background workflow failed: {e}", exc_info=True)
        sb.table("roadmaps").update({"status": "archived"}).eq("id", roadmap_id).execute()
        from db.supabase import log_agent_event
        log_agent_event(user_id, roadmap_id, "bg", "Workflow", "failed", str(e))


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/roadmap/{user_id}")
def get_roadmap(user_id: str):
    sb = get_supabase()
    r = sb.table("roadmaps").select("*").eq("user_id", user_id)\
        .eq("is_primary", True).neq("status", "archived")\
        .order("created_at", desc=True).limit(1).maybe_single().execute()
    if not r.data:
        return None
    roadmap = r.data
    # Fetch stages + tasks
    stages_r = sb.table("roadmap_stages").select("*")\
        .eq("roadmap_id", roadmap["id"]).order("stage_number").execute()
    stages = stages_r.data or []
    for stage in stages:
        tasks_r = sb.table("roadmap_tasks").select("*")\
            .eq("stage_id", stage["id"]).order("display_order").execute()
        stage["tasks"] = tasks_r.data or []
    roadmap["stages"] = stages
    return roadmap


@router.post("/roadmap/generate")
async def generate_roadmap(background_tasks: BackgroundTasks, data: dict = Body(...)):
    """Start the full 6-agent LangGraph pipeline in the background."""
    user_id = data.get("user_id")
    onet_code = data.get("onet_code")
    career_title = data.get("career_title", "Target Career")
    if not user_id:
        raise HTTPException(400, "user_id required")

    sb = get_supabase()
    profile = _build_profile_for_agent(user_id, sb)

    # Fetch selected career details
    career = {
        "onet_code": onet_code or "",
        "title": career_title,
    }
    if onet_code:
        occ_r = sb.table("onet_occupations").select("*").eq("onet_code", onet_code).maybe_single().execute()
        if occ_r.data:
            career.update(occ_r.data)
            career["title"] = occ_r.data.get("title", career_title)

    # Archive old primary roadmaps
    sb.table("roadmaps").update({"is_primary": False})\
        .eq("user_id", user_id).eq("is_primary", True).execute()

    # Create roadmap row
    roadmap_r = sb.table("roadmaps").insert({
        "user_id": user_id,
        "onet_code": onet_code,
        "target_career": career_title,
        "status": "generating",
        "is_primary": True,
        "weekly_hours": profile.get("weekly_hours", 10),
        "total_duration_months": profile.get("roadmap_duration_months", 12),
    }).execute()

    if not roadmap_r.data:
        raise HTTPException(500, "Failed to create roadmap record")

    roadmap_id = roadmap_r.data[0]["id"]
    session_id = str(uuid.uuid4())

    # Launch background pipeline
    background_tasks.add_task(
        asyncio.get_event_loop().create_task if asyncio.get_event_loop().is_running() else asyncio.run,
        _run_workflow_background(user_id, roadmap_id, career, profile)
    )

    # Also schedule as a plain background task with asyncio
    asyncio.create_task(_run_workflow_background(user_id, roadmap_id, career, profile))

    return {"roadmap_id": roadmap_id, "session_id": session_id, "status": "generating"}


@router.get("/roadmap/{roadmap_id}/stream")
async def stream_roadmap_events(roadmap_id: str):
    """SSE endpoint: stream agent execution events to frontend."""
    async def event_generator():
        sb = get_supabase()
        seen_ids: set[str] = set()
        no_data_count = 0
        max_wait_cycles = 120  # 60 seconds max

        while no_data_count < max_wait_cycles:
            # Check roadmap status
            r = sb.table("roadmaps").select("status").eq("id", roadmap_id).maybe_single().execute()
            status = r.data["status"] if r.data else "generating"

            # Fetch new agent logs
            logs_r = sb.table("agent_logs").select("*")\
                .eq("roadmap_id", roadmap_id)\
                .order("created_at").execute()

            new_events = [log for log in (logs_r.data or []) if log["id"] not in seen_ids]
            if new_events:
                no_data_count = 0
                for log in new_events:
                    seen_ids.add(log["id"])
                    import json
                    event_data = json.dumps({
                        "agent": log.get("agent_name", ""),
                        "status": log.get("status", ""),
                        "message": log.get("message", ""),
                        "timestamp": log.get("created_at", ""),
                    })
                    yield f"event: agent_update\ndata: {event_data}\n\n"
            else:
                no_data_count += 1

            if status == "active":
                import json
                yield f"event: complete\ndata: {json.dumps({'roadmap_id': roadmap_id})}\n\n"
                break
            elif status == "archived":
                yield f"event: error\ndata: {{\"message\": \"Roadmap generation failed\"}}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


@router.put("/roadmap/{roadmap_id}/task/{task_id}/complete")
def complete_task(roadmap_id: str, task_id: str):
    """Mark a task as completed and update stage progress."""
    sb = get_supabase()
    sb.table("roadmap_tasks").update({
        "is_completed": True,
        "completed_at": datetime.utcnow().isoformat(),
    }).eq("id", task_id).execute()

    # Recalculate stage completion
    task_r = sb.table("roadmap_tasks").select("stage_id").eq("id", task_id).maybe_single().execute()
    if task_r.data:
        stage_id = task_r.data["stage_id"]
        all_tasks = sb.table("roadmap_tasks").select("is_completed")\
            .eq("stage_id", stage_id).execute()
        tasks = all_tasks.data or []
        if tasks:
            pct = sum(1 for t in tasks if t["is_completed"]) / len(tasks) * 100
            new_status = "completed" if pct >= 100 else "in_progress"
            sb.table("roadmap_stages").update({
                "completion_percentage": pct,
                "status": new_status,
            }).eq("id", stage_id).execute()

            # Update overall roadmap %
            stage_r = sb.table("roadmap_stages").select("roadmap_id")\
                .eq("id", stage_id).maybe_single().execute()
            if stage_r.data:
                rm_id = stage_r.data["roadmap_id"]
                all_stages = sb.table("roadmap_stages").select("completion_percentage")\
                    .eq("roadmap_id", rm_id).execute()
                stages = all_stages.data or []
                if stages:
                    overall = sum(s["completion_percentage"] for s in stages) / len(stages)
                    sb.table("roadmaps").update({"completion_percentage": overall})\
                        .eq("id", rm_id).execute()

    return {"completed": True}


@router.put("/roadmap/{roadmap_id}/regenerate")
async def regenerate_roadmap(roadmap_id: str, background_tasks: BackgroundTasks):
    """Archive the current roadmap and generate a new one."""
    sb = get_supabase()
    r = sb.table("roadmaps").select("*").eq("id", roadmap_id).maybe_single().execute()
    if not r.data:
        raise HTTPException(404, "Roadmap not found")

    old = r.data
    user_id = old["user_id"]
    onet_code = old.get("onet_code", "")
    career_title = old.get("target_career", "Target Career")

    sb.table("roadmaps").update({"is_primary": False, "status": "archived"}).eq("id", roadmap_id).execute()

    profile = _build_profile_for_agent(user_id, sb)
    career = {"onet_code": onet_code, "title": career_title}
    if onet_code:
        occ = sb.table("onet_occupations").select("*").eq("onet_code", onet_code).maybe_single().execute()
        if occ.data:
            career.update(occ.data)

    new_r = sb.table("roadmaps").insert({
        "user_id": user_id,
        "onet_code": onet_code,
        "target_career": career_title,
        "status": "generating",
        "is_primary": True,
        "weekly_hours": profile.get("weekly_hours", 10),
        "total_duration_months": profile.get("roadmap_duration_months", 12),
        "generation_version": old.get("generation_version", 1) + 1,
    }).execute()

    new_roadmap_id = new_r.data[0]["id"]
    asyncio.create_task(_run_workflow_background(user_id, new_roadmap_id, career, profile))

    return {"roadmap_id": new_roadmap_id, "status": "generating"}


@router.get("/roadmap/{roadmap_id}/export")
def export_roadmap(roadmap_id: str):
    """Return full roadmap data for PDF generation."""
    sb = get_supabase()
    r = sb.table("roadmaps").select("*").eq("id", roadmap_id).maybe_single().execute()
    if not r.data:
        raise HTTPException(404, "Roadmap not found")
    roadmap = r.data
    stages_r = sb.table("roadmap_stages").select("*")\
        .eq("roadmap_id", roadmap_id).order("stage_number").execute()
    stages = stages_r.data or []
    for stage in stages:
        tasks_r = sb.table("roadmap_tasks").select("*")\
            .eq("stage_id", stage["id"]).order("display_order").execute()
        stage["tasks"] = tasks_r.data or []
    roadmap["stages"] = stages
    return roadmap
