"""
PathPilot AI — LangGraph Agent Workflow
Connects all 6 agents into a StateGraph with conditional retry logic.
"""
import asyncio
import logging
import uuid
from typing import Any

from langgraph.graph import StateGraph, END

from agents.state import AgentState
from agents.profile_analyzer import analyze_profile
from agents.career_discovery import discover_careers
from agents.skill_gap import analyze_skill_gap
from agents.learning_planner import plan_learning_path
from agents.resource_recommender import recommend_resources
from agents.roadmap_validator import validate_roadmap
from db.supabase import log_agent_event

logger = logging.getLogger(__name__)


# ── Conditional routing ────────────────────────────────────────────────────────

def should_retry_or_finish(state: AgentState) -> str:
    validation = state.get("validation_result", {})
    is_valid = validation.get("valid", True)
    retry_count = state.get("retry_count", 0)

    if not is_valid and retry_count < 2:
        return "replan"
    return "finish"


def increment_retry(state: AgentState) -> AgentState:
    """Increment retry counter before re-planning."""
    return {**state, "retry_count": state.get("retry_count", 0) + 1}


# ── Graph assembly ─────────────────────────────────────────────────────────────

workflow = StateGraph(AgentState)

workflow.add_node("profile_analyzer", analyze_profile)
workflow.add_node("career_discovery", discover_careers)
workflow.add_node("skill_gap", analyze_skill_gap)
workflow.add_node("learning_planner", plan_learning_path)
workflow.add_node("resource_recommender", recommend_resources)
workflow.add_node("roadmap_validator", validate_roadmap)
workflow.add_node("increment_retry", increment_retry)

workflow.set_entry_point("profile_analyzer")
workflow.add_edge("profile_analyzer", "career_discovery")
workflow.add_edge("career_discovery", "skill_gap")
workflow.add_edge("skill_gap", "learning_planner")
workflow.add_edge("learning_planner", "resource_recommender")
workflow.add_edge("resource_recommender", "roadmap_validator")
workflow.add_conditional_edges(
    "roadmap_validator",
    should_retry_or_finish,
    {
        "replan": "increment_retry",
        "finish": END,
    },
)
workflow.add_edge("increment_retry", "learning_planner")

app_graph = workflow.compile()


# ── Public entry point ─────────────────────────────────────────────────────────

async def run_roadmap_workflow(
    user_id: str,
    student_profile: dict[str, Any],
    selected_career: dict[str, Any],
    roadmap_id: str | None = None,
) -> AgentState:
    """
    Run the full LangGraph agent workflow.

    Args:
        user_id: Supabase user UUID
        student_profile: Full profile dict (skills, interests, experience, prefs)
        selected_career: Career dict with onet_code, title, etc.
        roadmap_id: Pre-created roadmap DB row ID (for event logging)

    Returns:
        Final agent state with all generated data
    """
    session_id = str(uuid.uuid4())

    initial_state: AgentState = {
        "user_id": user_id,
        "roadmap_id": roadmap_id,
        "session_id": session_id,
        "student_profile": student_profile,
        "career_matches": [],
        "selected_career": selected_career,
        "skill_gaps": [],
        "roadmap_stages": [],
        "resources": [],
        "validation_result": {},
        "agent_events": [],
        "error": None,
        "retry_count": 0,
    }

    logger.info(f"Starting roadmap workflow for user={user_id}, career={selected_career.get('title')}")

    try:
        final_state = await app_graph.ainvoke(initial_state)
        logger.info(f"Workflow complete. Stages: {len(final_state.get('roadmap_stages', []))}")
        return final_state
    except Exception as e:
        logger.error(f"Workflow error: {e}", exc_info=True)
        log_agent_event(
            user_id, roadmap_id, session_id, "Workflow", "failed",
            f"Workflow failed: {str(e)}"
        )
        return {**initial_state, "error": str(e)}
