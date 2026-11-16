from typing import TypedDict, Optional, List, Dict, Any


class AgentState(TypedDict):
    user_id: str
    roadmap_id: Optional[str]
    session_id: str  # For SSE event correlation
    student_profile: Dict[str, Any]
    career_matches: List[Dict[str, Any]]
    selected_career: Optional[Dict[str, Any]]
    skill_gaps: List[Dict[str, Any]]
    roadmap_stages: List[Dict[str, Any]]
    resources: List[Dict[str, Any]]
    validation_result: Dict[str, Any]
    agent_events: List[Dict[str, Any]]
    error: Optional[str]
    retry_count: int
