import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from collections import defaultdict

from config import get_settings

logger = logging.getLogger("pathpilot.db")

# Fallback in-memory stores for offline development / mock modes
_MEM_AGENT_EVENTS = defaultdict(list)
_MEM_ROADMAPS = {}
_MEM_CAREER_RECOMMENDATIONS = defaultdict(list)
_MEM_SKILL_GAPS = {}

# Built-in sample O*NET Occupations (for fallback or fast querying)
SAMPLE_ONET_OCCUPATIONS: List[Dict[str, Any]] = [
    {
        "onet_code": "15-2051.00",
        "title": "Data Scientists",
        "description": "Develop and implement a set of techniques or analytics applications to transform raw data into meaningful information using data-oriented programming languages and visualization software.",
        "job_zone": 5,
        "bright_outlook": True,
        "green_economy": False,
        "median_annual_wage": 108020,
        "typical_education": "Bachelor's degree",
        "sample_jobs": ["Data Scientist", "Applied Scientist", "Machine Learning Specialist"]
    },
    {
        "onet_code": "15-2051.01",
        "title": "Business Intelligence Analysts",
        "description": "Produce financial and market intelligence by querying data repositories and generating periodic reports.",
        "job_zone": 4,
        "bright_outlook": True,
        "green_economy": False,
        "median_annual_wage": 99150,
        "typical_education": "Bachelor's degree",
        "sample_jobs": ["BI Analyst", "BI Consultant", "Business Intelligence Architect"]
    },
    {
        "onet_code": "15-1252.00",
        "title": "Software Developers",
        "description": "Research, design, and develop computer and network software or specialized utility programs.",
        "job_zone": 4,
        "bright_outlook": True,
        "green_economy": False,
        "median_annual_wage": 132270,
        "typical_education": "Bachelor's degree",
        "sample_jobs": ["Software Engineer", "Backend Developer", "Full Stack Developer"]
    },
    {
        "onet_code": "15-1254.00",
        "title": "Web Developers",
        "description": "Design, create, and modify Web sites. Analyze user needs to implement Web site content, graphics, performance, and capacity.",
        "job_zone": 3,
        "bright_outlook": True,
        "green_economy": False,
        "median_annual_wage": 78580,
        "typical_education": "Associate's degree",
        "sample_jobs": ["Frontend Developer", "Webmaster", "UI Engineer"]
    },
    {
        "onet_code": "15-1212.00",
        "title": "Information Security Analysts",
        "description": "Plan, implement, upgrade, or monitor security measures for the protection of computer networks and information.",
        "job_zone": 4,
        "bright_outlook": True,
        "green_economy": False,
        "median_annual_wage": 120360,
        "typical_education": "Bachelor's degree",
        "sample_jobs": ["Cybersecurity Analyst", "Security Engineer", "Information Assurance Specialist"]
    },
    {
        "onet_code": "15-1242.00",
        "title": "Database Architects",
        "description": "Design strategies for enterprise database systems and set standards for operations, programming, and security.",
        "job_zone": 5,
        "bright_outlook": False,
        "green_economy": False,
        "median_annual_wage": 130680,
        "typical_education": "Bachelor's degree",
        "sample_jobs": ["Database Architect", "Data Modeler", "Data Warehouse Architect"]
    },
    {
        "onet_code": "15-1255.01",
        "title": "User Experience Researchers",
        "description": "Conduct user research to understand behaviors, needs, and motivations through observation, task analysis, and feedback methodologies.",
        "job_zone": 4,
        "bright_outlook": True,
        "green_economy": False,
        "median_annual_wage": 93010,
        "typical_education": "Bachelor's degree",
        "sample_jobs": ["UX Researcher", "Usability Analyst", "Product Researcher"]
    },
    {
        "onet_code": "15-1221.00",
        "title": "Computer and Information Research Scientists",
        "description": "Conduct research into fundamental computer and information science as theorists, designers, or inventors.",
        "job_zone": 5,
        "bright_outlook": True,
        "green_economy": False,
        "median_annual_wage": 136620,
        "typical_education": "Master's degree",
        "sample_jobs": ["AI Researcher", "Computer Scientist", "Algorithm Specialist"]
    },
    {
        "onet_code": "15-2031.00",
        "title": "Operations Research Analysts",
        "description": "Formulate and apply mathematical modeling and other optimizing methods to develop and interpret information that assists management with decisionmaking.",
        "job_zone": 4,
        "bright_outlook": True,
        "green_economy": False,
        "median_annual_wage": 83610,
        "typical_education": "Bachelor's degree",
        "sample_jobs": ["Operations Analyst", "Decision Analyst", "Analytics Scientist"]
    },
    {
        "onet_code": "11-3021.00",
        "title": "Computer and Information Systems Managers",
        "description": "Plan, direct, or coordinate activities in such fields as electronic data processing, information systems, systems analysis, and computer programming.",
        "job_zone": 5,
        "bright_outlook": False,
        "green_economy": False,
        "median_annual_wage": 164070,
        "typical_education": "Bachelor's degree",
        "sample_jobs": ["IT Director", "Engineering Manager", "Chief Technology Officer"]
    }
]

SAMPLE_ONET_SKILLS: Dict[str, List[Dict[str, Any]]] = {
    "15-2051.00": [
        {"skill_name": "Programming (Python, R, SQL)", "importance": 90.0, "level": 5.5, "skill_category": "technical"},
        {"skill_name": "Mathematics & Statistics", "importance": 88.0, "level": 5.5, "skill_category": "basic"},
        {"skill_name": "Machine Learning & Algorithms", "importance": 85.0, "level": 5.0, "skill_category": "technical"},
        {"skill_name": "Data Visualization & Storytelling", "importance": 80.0, "level": 4.5, "skill_category": "technical"},
        {"skill_name": "Critical Thinking", "importance": 82.5, "level": 5.0, "skill_category": "basic"},
        {"skill_name": "Complex Problem Solving", "importance": 85.0, "level": 5.2, "skill_category": "cross_functional"},
        {"skill_name": "Data Wrangling & ETL", "importance": 78.0, "level": 4.5, "skill_category": "technical"},
        {"skill_name": "Deep Learning & Neural Networks", "importance": 75.0, "level": 4.5, "skill_category": "technical"}
    ],
    "15-1252.00": [
        {"skill_name": "Programming (TypeScript, Python, Java, Go)", "importance": 95.0, "level": 6.0, "skill_category": "technical"},
        {"skill_name": "Software Architecture & Design Patterns", "importance": 88.0, "level": 5.2, "skill_category": "technical"},
        {"skill_name": "API Design & REST/GraphQL", "importance": 85.0, "level": 5.0, "skill_category": "technical"},
        {"skill_name": "Database Management & SQL", "importance": 82.0, "level": 4.8, "skill_category": "technical"},
        {"skill_name": "Version Control & Git Workflow", "importance": 80.0, "level": 4.5, "skill_category": "tool"},
        {"skill_name": "Testing & Test-Driven Development", "importance": 78.0, "level": 4.5, "skill_category": "technical"},
        {"skill_name": "Complex Problem Solving", "importance": 86.0, "level": 5.0, "skill_category": "cross_functional"},
        {"skill_name": "DevOps & CI/CD Pipelines", "importance": 72.0, "level": 4.0, "skill_category": "technical"}
    ],
    "15-1254.00": [
        {"skill_name": "JavaScript & TypeScript", "importance": 92.0, "level": 5.2, "skill_category": "technical"},
        {"skill_name": "HTML5 & CSS3 / Modern Styling", "importance": 90.0, "level": 5.0, "skill_category": "technical"},
        {"skill_name": "Modern Frontend Frameworks (React, Next.js, Vue)", "importance": 88.0, "level": 5.0, "skill_category": "technical"},
        {"skill_name": "Responsive Design & Accessibility", "importance": 82.0, "level": 4.5, "skill_category": "technical"},
        {"skill_name": "Web Performance Optimization", "importance": 75.0, "level": 4.2, "skill_category": "technical"},
        {"skill_name": "API Integration", "importance": 80.0, "level": 4.5, "skill_category": "technical"}
    ],
    "15-1212.00": [
        {"skill_name": "Network & System Security", "importance": 92.0, "level": 5.5, "skill_category": "technical"},
        {"skill_name": "Vulnerability Assessment & Threat Analysis", "importance": 90.0, "level": 5.2, "skill_category": "technical"},
        {"skill_name": "Security Protocols & Cryptography", "importance": 85.0, "level": 5.0, "skill_category": "technical"},
        {"skill_name": "Incident Response & Forensics", "importance": 82.0, "level": 4.8, "skill_category": "technical"},
        {"skill_name": "Security Compliance & Frameworks (NIST, ISO)", "importance": 78.0, "level": 4.5, "skill_category": "basic"}
    ]
}

SAMPLE_ONET_TECH: Dict[str, List[Dict[str, Any]]] = {
    "15-2051.00": [
        {"technology_name": "Python", "technology_category": "Development environment software", "is_hot_technology": True},
        {"technology_name": "SQL", "technology_category": "Database management system software", "is_hot_technology": True},
        {"technology_name": "TensorFlow", "technology_category": "Development environment software", "is_hot_technology": True},
        {"technology_name": "PyTorch", "technology_category": "Development environment software", "is_hot_technology": True},
        {"technology_name": "Pandas / NumPy", "technology_category": "Analytical or scientific software", "is_hot_technology": True},
        {"technology_name": "Docker", "technology_category": "Platform software", "is_hot_technology": True}
    ],
    "15-1252.00": [
        {"technology_name": "JavaScript / TypeScript", "technology_category": "Development environment software", "is_hot_technology": True},
        {"technology_name": "React / Next.js", "technology_category": "Web platform development software", "is_hot_technology": True},
        {"technology_name": "Node.js / Express / FastAPI", "technology_category": "Development environment software", "is_hot_technology": True},
        {"technology_name": "PostgreSQL", "technology_category": "Database management system software", "is_hot_technology": True},
        {"technology_name": "Git / GitHub", "technology_category": "Configuration management software", "is_hot_technology": True},
        {"technology_name": "Docker & Kubernetes", "technology_category": "Platform software", "is_hot_technology": True}
    ]
}

_supabase_client = None

def get_supabase():
    """
    Returns the Supabase Client configured with the Service Role key.
    Falls back gracefully to None if credentials are not configured.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    
    settings = get_settings()
    url = settings.supabase_url.strip()
    key = (settings.supabase_service_role_key or settings.supabase_anon_key or "").strip()
    
    if not url or not key or "your-project-id" in url:
        logger.warning("Supabase credentials not configured or using default placeholders. Running in mock/local mode.")
        return None
    
    try:
        from supabase import create_client, Client
        _supabase_client = create_client(url, key)
        return _supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None


async def fetch_onet_occupation(onet_code: str) -> Optional[Dict[str, Any]]:
    """Fetch O*NET occupation by ONET code."""
    client = get_supabase()
    if client:
        try:
            resp = client.table("onet_occupations").select("*").eq("onet_code", onet_code).execute()
            if resp.data and len(resp.data) > 0:
                return resp.data[0]
        except Exception as e:
            logger.warning(f"Error fetching occupation {onet_code} from Supabase: {e}")
    
    # Fallback to sample data
    for occ in SAMPLE_ONET_OCCUPATIONS:
        if occ["onet_code"] == onet_code:
            return occ
    return None


async def fetch_onet_skills(onet_code: str) -> List[Dict[str, Any]]:
    """Fetch O*NET skills for a specific occupation."""
    client = get_supabase()
    if client:
        try:
            resp = client.table("onet_skills").select("*").eq("onet_code", onet_code).order("importance", desc=True).execute()
            if resp.data and len(resp.data) > 0:
                return resp.data
        except Exception as e:
            logger.warning(f"Error fetching skills for {onet_code} from Supabase: {e}")
    
    # Fallback to sample skills
    if onet_code in SAMPLE_ONET_SKILLS:
        return SAMPLE_ONET_SKILLS[onet_code]
    return SAMPLE_ONET_SKILLS.get("15-2051.00", [])


async def fetch_onet_technology(onet_code: str) -> List[Dict[str, Any]]:
    """Fetch technology tools and frameworks for an occupation."""
    client = get_supabase()
    if client:
        try:
            resp = client.table("onet_technology").select("*").eq("onet_code", onet_code).execute()
            if resp.data and len(resp.data) > 0:
                return resp.data
        except Exception as e:
            logger.warning(f"Error fetching technology for {onet_code} from Supabase: {e}")
    
    return SAMPLE_ONET_TECH.get(onet_code, SAMPLE_ONET_TECH.get("15-2051.00", []))


async def search_onet_occupations(query: str) -> List[Dict[str, Any]]:
    """Search O*NET occupations by keyword/query."""
    query_clean = query.strip().lower()
    client = get_supabase()
    if client:
        try:
            resp = client.table("onet_occupations").select("*").ilike("title", f"%{query_clean}%").limit(20).execute()
            if resp.data and len(resp.data) > 0:
                return resp.data
        except Exception as e:
            logger.warning(f"Error searching occupations in Supabase: {e}")
    
    # Fallback search
    results = []
    for occ in SAMPLE_ONET_OCCUPATIONS:
        if (query_clean in occ["title"].lower() or 
            query_clean in occ.get("description", "").lower() or 
            query_clean in occ["onet_code"]):
            results.append(occ)
    return results if results else SAMPLE_ONET_OCCUPATIONS[:5]


async def get_bright_outlook_occupations() -> List[Dict[str, Any]]:
    """Get occupations with Bright Outlook designation."""
    client = get_supabase()
    if client:
        try:
            resp = client.table("onet_occupations").select("*").eq("bright_outlook", True).limit(25).execute()
            if resp.data and len(resp.data) > 0:
                return resp.data
        except Exception as e:
            logger.warning(f"Error fetching bright outlook occupations from Supabase: {e}")
    
    return [occ for occ in SAMPLE_ONET_OCCUPATIONS if occ.get("bright_outlook", False)]


async def save_career_recommendations(user_id: str, recommendations: List[Dict[str, Any]]) -> None:
    """Save generated career recommendations for a user."""
    client = get_supabase()
    rows = []
    for rec in recommendations:
        rows.append({
            "id": rec.get("id") or str(uuid.uuid4()),
            "user_id": user_id,
            "onet_code": rec.get("onet_code"),
            "career_title": rec.get("career_title") or rec.get("title", ""),
            "suitability_score": float(rec.get("suitability_score", 85.0)),
            "match_explanation": rec.get("match_explanation", ""),
            "matching_skills": rec.get("matching_skills", []),
            "missing_skills": rec.get("missing_skills", []),
            "is_selected": rec.get("is_selected", False),
            "generation_version": rec.get("generation_version", 1)
        })
    
    # Store in memory cache
    _MEM_CAREER_RECOMMENDATIONS[user_id] = rows
    
    if client:
        try:
            # Delete previous unselected recommendations for this user to keep it clean
            client.table("career_recommendations").delete().eq("user_id", user_id).execute()
            client.table("career_recommendations").insert(rows).execute()
        except Exception as e:
            logger.error(f"Error saving career recommendations to Supabase: {e}")


async def save_roadmap(user_id: str, roadmap_data: Dict[str, Any]) -> str:
    """
    Save full roadmap tree: roadmap, stages, tasks, milestones.
    Returns the created roadmap_id.
    """
    roadmap_id = roadmap_data.get("id") or str(uuid.uuid4())
    client = get_supabase()
    
    roadmap_row = {
        "id": roadmap_id,
        "user_id": user_id,
        "onet_code": roadmap_data.get("onet_code"),
        "target_career": roadmap_data.get("target_career") or roadmap_data.get("title", "Career Roadmap"),
        "total_duration_months": roadmap_data.get("total_duration_months", 6),
        "weekly_hours": roadmap_data.get("weekly_hours", 10),
        "status": roadmap_data.get("status", "active"),
        "completion_percentage": float(roadmap_data.get("completion_percentage", 0.0)),
        "is_primary": True,
        "generation_version": roadmap_data.get("generation_version", 1)
    }
    
    stages_to_insert = []
    tasks_to_insert = []
    milestones_to_insert = []
    
    raw_stages = roadmap_data.get("stages", []) or roadmap_data.get("roadmap_stages", [])
    raw_resources = roadmap_data.get("resources", [])
    
    for idx, stage in enumerate(raw_stages):
        stage_id = stage.get("id") or str(uuid.uuid4())
        stage_num = stage.get("stage_number", idx + 1)
        
        stages_to_insert.append({
            "id": stage_id,
            "roadmap_id": roadmap_id,
            "stage_number": stage_num,
            "stage_title": stage.get("stage_title") or stage.get("title", f"Stage {stage_num}"),
            "stage_description": stage.get("stage_description") or stage.get("description", ""),
            "skills_to_learn": stage.get("skills_to_learn", []),
            "prerequisites": stage.get("prerequisites", []),
            "duration_weeks": stage.get("duration_weeks", 4),
            "status": "in_progress" if idx == 0 else "locked",
            "completion_percentage": 0.0
        })
        
        # Check tasks within stage or from resources list
        stage_tasks = stage.get("tasks", [])
        if not stage_tasks and idx < len(raw_resources):
            stage_res = raw_resources[idx]
            # Convert courses, projects, certs to tasks
            for c in stage_res.get("courses", []):
                stage_tasks.append({
                    "task_type": "course",
                    "title": c.get("title", "Online Course"),
                    "description": f"Learn foundational skills on {c.get('platform', 'online platform')}",
                    "platform": c.get("platform", "Coursera"),
                    "url": c.get("url_hint", "https://coursera.org"),
                    "duration_hours": c.get("duration_hours", 20),
                    "difficulty": c.get("difficulty", "intermediate").lower(),
                    "skills_covered": stage.get("skills_to_learn", [])[:2],
                    "source": "ai_recommended"
                })
            for p in stage_res.get("projects", []):
                stage_tasks.append({
                    "task_type": "project",
                    "title": p.get("title", "Hands-on Project"),
                    "description": p.get("description", "Build a real-world application"),
                    "duration_hours": p.get("estimated_hours", 15),
                    "difficulty": "intermediate",
                    "skills_covered": p.get("skills_covered", stage.get("skills_to_learn", [])),
                    "source": "ai_recommended"
                })
            for cert in stage_res.get("certifications", []):
                stage_tasks.append({
                    "task_type": "certification",
                    "title": cert.get("name", "Industry Certificate"),
                    "platform": cert.get("provider", "Industry Standard"),
                    "url": cert.get("url_hint", ""),
                    "duration_hours": 30,
                    "difficulty": "advanced",
                    "skills_covered": stage.get("skills_to_learn", []),
                    "source": "ai_recommended"
                })
        
        for t_idx, task in enumerate(stage_tasks):
            tasks_to_insert.append({
                "id": task.get("id") or str(uuid.uuid4()),
                "stage_id": stage_id,
                "task_type": task.get("task_type", "course"),
                "title": task.get("title", f"Task {t_idx+1}"),
                "description": task.get("description", ""),
                "url": task.get("url", ""),
                "platform": task.get("platform", ""),
                "duration_hours": task.get("duration_hours", 10),
                "difficulty": task.get("difficulty", "intermediate"),
                "skills_covered": task.get("skills_covered", []),
                "is_required": task.get("is_required", True),
                "is_completed": task.get("is_completed", False),
                "source": task.get("source", "ai_recommended"),
                "display_order": t_idx
            })
            
        # Add milestone for stage completion
        milestones_to_insert.append({
            "id": str(uuid.uuid4()),
            "roadmap_id": roadmap_id,
            "stage_id": stage_id,
            "title": f"Complete {stage.get('stage_title') or stage.get('title', f'Stage {stage_num}')}",
            "description": f"Master competencies: {', '.join(stage.get('skills_to_learn', [])[:3])}",
            "milestone_type": "project" if idx % 2 == 1 else "skill",
            "is_achieved": False,
            "display_order": stage_num
        })

    # Save to memory store
    _MEM_ROADMAPS[roadmap_id] = {
        **roadmap_row,
        "stages": [
            {
                **s,
                "tasks": [t for t in tasks_to_insert if t["stage_id"] == s["id"]]
            }
            for s in stages_to_insert
        ],
        "milestones": milestones_to_insert
    }
    
    if client:
        try:
            # Set other roadmaps for user to not primary
            client.table("roadmaps").update({"is_primary": False}).eq("user_id", user_id).execute()
            # Upsert roadmap
            client.table("roadmaps").upsert(roadmap_row).execute()
            if stages_to_insert:
                client.table("roadmap_stages").upsert(stages_to_insert).execute()
            if tasks_to_insert:
                client.table("roadmap_tasks").upsert(tasks_to_insert).execute()
            if milestones_to_insert:
                client.table("milestones").upsert(milestones_to_insert).execute()
            logger.info(f"Successfully saved roadmap {roadmap_id} to Supabase")
        except Exception as e:
            logger.error(f"Error saving roadmap to Supabase: {e}")
            
    return roadmap_id


async def save_skill_gap(user_id: str, roadmap_id: Optional[str], gaps: List[Dict[str, Any]], onet_code: Optional[str] = None) -> str:
    """Save skill gap analysis and individual items."""
    analysis_id = str(uuid.uuid4())
    client = get_supabase()
    
    analysis_row = {
        "id": analysis_id,
        "user_id": user_id,
        "roadmap_id": roadmap_id,
        "onet_code": onet_code,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    items_to_insert = []
    for idx, gap in enumerate(gaps):
        items_to_insert.append({
            "id": gap.get("id") or str(uuid.uuid4()),
            "analysis_id": analysis_id,
            "skill_name": gap.get("skill_name", "Skill"),
            "student_level": float(gap.get("student_level", 1.0)),
            "required_level": float(gap.get("required_level", 4.0)),
            "gap_category": gap.get("gap_category", "must_learn"),
            "onet_importance": float(gap.get("onet_importance", 80.0)),
            "priority": int(gap.get("priority", idx + 1))
        })
        
    _MEM_SKILL_GAPS[analysis_id] = {
        **analysis_row,
        "items": items_to_insert
    }
    
    if client:
        try:
            client.table("skill_gap_analyses").insert(analysis_row).execute()
            if items_to_insert:
                client.table("skill_gap_items").insert(items_to_insert).execute()
        except Exception as e:
            logger.error(f"Error saving skill gap to Supabase: {e}")
            
    return analysis_id


async def log_agent_event(
    user_id: Optional[str],
    roadmap_id: Optional[str],
    session_id: str,
    agent_name: str,
    status: str,
    message: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an agent execution step.
    Saves to DB and in-memory list for instant SSE streaming.
    """
    event_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()
    event_data = {
        "id": event_id,
        "user_id": user_id,
        "roadmap_id": roadmap_id,
        "session_id": session_id,
        "agent_name": agent_name,
        "status": status,
        "message": message,
        "metadata": metadata or {},
        "created_at": ts
    }
    
    # Store in session event queue
    _MEM_AGENT_EVENTS[session_id].append(event_data)
    
    client = get_supabase()
    if client and user_id:
        try:
            client.table("agent_logs").insert(event_data).execute()
        except Exception as e:
            logger.warning(f"Failed to persist agent log to Supabase: {e}")


async def get_latest_agent_events(session_id: str, after_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all agent events for a session after a given event id."""
    events = _MEM_AGENT_EVENTS.get(session_id, [])
    if not after_id:
        return list(events)
    
    result = []
    found = False
    for ev in events:
        if found:
            result.append(ev)
        elif ev["id"] == after_id:
            found = True
    return result
