"""
PathPilot AI — Resource Recommender Agent
Agent 5: Recommends courses, projects, and certifications per stage.
"""
import json
import logging
from typing import Any

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from agents.state import AgentState
from config import get_settings
from db.supabase import log_agent_event

logger = logging.getLogger(__name__)
settings = get_settings()

AGENT_NAME = "Resource Recommender"

MOCK_RESOURCES = {
    "default_courses": [
        {"title": "Complete Python Bootcamp", "platform": "Udemy", "url_hint": "udemy.com/python-bootcamp", "duration_hours": 22, "difficulty": "beginner"},
        {"title": "Machine Learning Specialization", "platform": "Coursera", "url_hint": "coursera.org/ml-specialization", "duration_hours": 60, "difficulty": "intermediate"},
    ],
    "default_projects": [
        {"title": "Build a Data Analysis Dashboard", "description": "Analyze a public dataset and create visualizations", "skills_covered": [], "estimated_hours": 10},
    ]
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def _call_gemini(prompt: str) -> str:
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text


def recommend_resources(state: AgentState) -> AgentState:
    """Generate courses, projects, and certifications per roadmap stage."""
    user_id = state["user_id"]
    session_id = state["session_id"]
    roadmap_id = state.get("roadmap_id")
    stages = state.get("roadmap_stages", [])
    selected_career = state.get("selected_career", {})
    profile = state.get("student_profile", {})

    log_agent_event(
        user_id, roadmap_id, session_id, AGENT_NAME, "started",
        f"Finding courses and projects for {len(stages)} stages..."
    )

    if not settings.gemini_api_key or not stages:
        # Mock resources
        resources = []
        for stage in stages:
            resources.append({
                "stage_number": stage["stage_number"],
                "courses": MOCK_RESOURCES["default_courses"],
                "projects": MOCK_RESOURCES["default_projects"],
                "certifications": [],
            })
        log_agent_event(user_id, roadmap_id, session_id, AGENT_NAME, "completed",
                        "Resources generated (demo mode).")
        return {**state, "resources": resources}

    all_resources = []

    for stage in stages:
        stage_num = stage["stage_number"]
        stage_title = stage["stage_title"]
        skills = stage.get("skills_to_learn", [])
        duration_weeks = stage.get("duration_weeks", 4)

        log_agent_event(
            user_id, roadmap_id, session_id, AGENT_NAME, "running",
            f"Recommending resources for Stage {stage_num}: {stage_title}..."
        )

        prompt = f"""You are a learning resource curator. Recommend specific, real resources for a career roadmap stage.

CAREER GOAL: {selected_career.get('title', 'Software Professional')}
STUDENT LEVEL: {profile.get('experience_level', 2)}/5

STAGE {stage_num}: {stage_title}
Skills to learn: {', '.join(skills)}
Duration available: {duration_weeks} weeks

RULES:
1. Recommend ONLY real, well-known platforms (Coursera, Udemy, YouTube, freeCodeCamp, edX, LinkedIn Learning, Pluralsight, MIT OpenCourseWare, Khan Academy, fast.ai)
2. Use realistic course names (can be actual course names you know)
3. For projects: make them practical and portfolio-worthy
4. All resources are AI-recommended (not from O*NET)
5. Keep duration realistic

Return ONLY valid JSON (no markdown):
{{
  "courses": [
    {{
      "title": "Exact course name",
      "platform": "Platform name",
      "url_hint": "platform.com/course-path",
      "duration_hours": 20,
      "difficulty": "beginner|intermediate|advanced",
      "skills_covered": ["skill1"]
    }}
  ],
  "projects": [
    {{
      "title": "Project title",
      "description": "2-3 sentence project description with clear deliverable",
      "skills_covered": ["skill1"],
      "estimated_hours": 15
    }}
  ],
  "certifications": [
    {{
      "name": "Certification name",
      "provider": "Provider name",
      "url_hint": "provider.com/cert"
    }}
  ]
}}

Provide 2-3 courses, 1-2 projects, 0-1 certifications (only add cert if highly relevant)."""

        try:
            raw = _call_gemini(prompt)
            raw = raw.strip()
            if raw.startswith("```"):
                parts = raw.split("```")
                raw = parts[1] if len(parts) > 1 else parts[0]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip().rstrip("```").strip()

            data = json.loads(raw)
            all_resources.append({
                "stage_number": stage_num,
                "courses": data.get("courses", []),
                "projects": data.get("projects", []),
                "certifications": data.get("certifications", []),
            })

        except Exception as e:
            logger.warning(f"Resource recommendation failed for stage {stage_num}: {e}")
            all_resources.append({
                "stage_number": stage_num,
                "courses": MOCK_RESOURCES["default_courses"][:2],
                "projects": MOCK_RESOURCES["default_projects"][:1],
                "certifications": [],
            })

    log_agent_event(
        user_id, roadmap_id, session_id, AGENT_NAME, "completed",
        f"Recommended resources for all {len(stages)} stages. "
        f"Total: {sum(len(r['courses']) for r in all_resources)} courses, "
        f"{sum(len(r['projects']) for r in all_resources)} projects."
    )

    return {**state, "resources": all_resources}
