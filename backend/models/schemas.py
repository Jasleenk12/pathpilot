from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class GapCategory(str, Enum):
    acquired = "acquired"
    needs_improvement = "needs_improvement"
    must_learn = "must_learn"


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ============================================================
# SKILLS, INTERESTS, EXPERIENCE
# ============================================================

class StudentSkill(BaseSchema):
    id: Optional[str] = None
    user_id: Optional[str] = None
    skill_name: str
    skill_category: Optional[str] = "technical"
    proficiency_level: int = Field(default=1, ge=1, le=5)
    years_experience: Optional[float] = 0.0
    is_current: Optional[bool] = True
    created_at: Optional[str] = None


class CreateSkillRequest(BaseSchema):
    skill_name: str
    skill_category: Optional[str] = "technical"
    proficiency_level: Optional[int] = Field(default=1, ge=1, le=5)
    years_experience: Optional[float] = 0.0


class StudentInterest(BaseSchema):
    id: Optional[str] = None
    user_id: Optional[str] = None
    interest: str
    interest_type: Optional[str] = "technology"
    created_at: Optional[str] = None


class CreateInterestRequest(BaseSchema):
    interest: str
    interest_type: Optional[str] = "technology"


class StudentExperience(BaseSchema):
    id: Optional[str] = None
    user_id: Optional[str] = None
    experience_type: Optional[str] = "project"
    title: str
    organization: Optional[str] = None
    description: Optional[str] = None
    technologies_used: Optional[List[str]] = []
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_ongoing: Optional[bool] = False
    created_at: Optional[str] = None


class CreateExperienceRequest(BaseSchema):
    experience_type: Optional[str] = "project"
    title: str
    organization: Optional[str] = None
    description: Optional[str] = None
    technologies_used: Optional[List[str]] = []
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_ongoing: Optional[bool] = False


# ============================================================
# STUDENT PROFILE
# ============================================================

class StudentProfile(BaseSchema):
    id: Optional[str] = None
    full_name: str
    email: str
    degree: Optional[str] = None
    specialization: Optional[str] = None
    education_level: Optional[str] = None
    graduation_year: Optional[int] = None
    university: Optional[str] = None
    weekly_hours: Optional[int] = 10
    roadmap_duration_months: Optional[int] = 12
    preferred_roles: Optional[List[str]] = []
    career_goals: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    onboarding_completed: Optional[bool] = False
    skills: Optional[List[StudentSkill]] = []
    interests: Optional[List[StudentInterest]] = []
    experiences: Optional[List[StudentExperience]] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CreateProfileRequest(BaseSchema):
    id: Optional[str] = None
    full_name: str
    email: str
    degree: Optional[str] = None
    specialization: Optional[str] = None
    education_level: Optional[str] = None
    graduation_year: Optional[int] = None
    university: Optional[str] = None
    weekly_hours: Optional[int] = 10
    roadmap_duration_months: Optional[int] = 12
    preferred_roles: Optional[List[str]] = []
    career_goals: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None


class UpdateProfileRequest(BaseSchema):
    full_name: Optional[str] = None
    email: Optional[str] = None
    degree: Optional[str] = None
    specialization: Optional[str] = None
    education_level: Optional[str] = None
    graduation_year: Optional[int] = None
    university: Optional[str] = None
    weekly_hours: Optional[int] = None
    roadmap_duration_months: Optional[int] = None
    preferred_roles: Optional[List[str]] = None
    career_goals: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    onboarding_completed: Optional[bool] = None


class OnboardingRequest(BaseSchema):
    full_name: Optional[str] = None
    degree: Optional[str] = None
    specialization: Optional[str] = None
    education_level: Optional[str] = None
    graduation_year: Optional[int] = None
    university: Optional[str] = None
    weekly_hours: Optional[int] = 10
    roadmap_duration_months: Optional[int] = 12
    preferred_roles: Optional[List[str]] = []
    career_goals: Optional[str] = None
    skills: Optional[List[CreateSkillRequest]] = []
    interests: Optional[List[CreateInterestRequest]] = []
    experiences: Optional[List[CreateExperienceRequest]] = []


# ============================================================
# CAREER RECOMMENDATIONS
# ============================================================

class CareerRecommendation(BaseSchema):
    id: Optional[str] = None
    user_id: Optional[str] = None
    onet_code: Optional[str] = None
    career_title: str
    suitability_score: float = 85.0
    match_explanation: Optional[str] = None
    matching_skills: Optional[List[str]] = []
    missing_skills: Optional[List[str]] = []
    is_selected: Optional[bool] = False
    generation_version: Optional[int] = 1
    created_at: Optional[str] = None


class CareerRecommendationResponse(BaseSchema):
    recommendations: List[CareerRecommendation]


class GenerateRecommendationsRequest(BaseSchema):
    user_id: Optional[str] = None


class SelectCareerRequest(BaseSchema):
    onet_code: str


# ============================================================
# SKILL GAP ANALYSIS
# ============================================================

class SkillGapItem(BaseSchema):
    id: Optional[str] = None
    analysis_id: Optional[str] = None
    skill_name: str
    student_level: Optional[float] = 1.0
    required_level: Optional[float] = 4.0
    gap_category: GapCategory = GapCategory.must_learn
    onet_importance: Optional[float] = 80.0
    priority: Optional[int] = 1


class SkillGapAnalysisResponse(BaseSchema):
    id: Optional[str] = None
    user_id: Optional[str] = None
    roadmap_id: Optional[str] = None
    onet_code: Optional[str] = None
    gaps: List[SkillGapItem] = []


# ============================================================
# ROADMAP & TASKS
# ============================================================

class RoadmapTask(BaseSchema):
    id: Optional[str] = None
    stage_id: Optional[str] = None
    task_type: Optional[str] = "course"
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    platform: Optional[str] = None
    duration_hours: Optional[int] = 10
    difficulty: Optional[str] = "intermediate"
    skills_covered: Optional[List[str]] = []
    is_required: Optional[bool] = True
    is_completed: Optional[bool] = False
    completed_at: Optional[str] = None
    source: Optional[str] = "ai_recommended"
    display_order: Optional[int] = 0


class RoadmapStage(BaseSchema):
    id: Optional[str] = None
    roadmap_id: Optional[str] = None
    stage_number: int = 1
    stage_title: str
    stage_description: Optional[str] = None
    skills_to_learn: Optional[List[str]] = []
    prerequisites: Optional[List[str]] = []
    duration_weeks: Optional[int] = 4
    status: Optional[str] = "locked"
    completion_percentage: Optional[float] = 0.0
    tasks: Optional[List[RoadmapTask]] = []


class MilestoneStatus(BaseSchema):
    id: Optional[str] = None
    roadmap_id: Optional[str] = None
    stage_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    milestone_type: Optional[str] = "project"
    is_achieved: Optional[bool] = False
    achieved_at: Optional[str] = None
    display_order: Optional[int] = 0


class Roadmap(BaseSchema):
    id: Optional[str] = None
    user_id: str
    career_recommendation_id: Optional[str] = None
    onet_code: Optional[str] = None
    target_career: str
    total_duration_months: Optional[int] = 6
    weekly_hours: Optional[int] = 10
    status: Optional[str] = "active"
    completion_percentage: Optional[float] = 0.0
    is_primary: Optional[bool] = True
    generation_version: Optional[int] = 1
    stages: Optional[List[RoadmapStage]] = []
    milestones: Optional[List[MilestoneStatus]] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class GenerateRoadmapRequest(BaseSchema):
    user_id: str
    onet_code: Optional[str] = None
    target_career: Optional[str] = None
    weekly_hours: Optional[int] = None
    roadmap_duration_months: Optional[int] = None


class RoadmapExport(BaseSchema):
    roadmap: Roadmap
    skill_gaps: Optional[List[SkillGapItem]] = []
    milestones: Optional[List[MilestoneStatus]] = []
    profile: Optional[Dict[str, Any]] = None


# ============================================================
# CHAT
# ============================================================

class ChatMessage(BaseSchema):
    id: Optional[str] = None
    session_id: Optional[str] = None
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = {}
    created_at: Optional[str] = None


class ChatSession(BaseSchema):
    id: Optional[str] = None
    user_id: str
    roadmap_id: Optional[str] = None
    session_title: Optional[str] = "New Conversation"
    is_active: Optional[bool] = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    messages: Optional[List[ChatMessage]] = []


class CreateChatSessionRequest(BaseSchema):
    user_id: str
    roadmap_id: Optional[str] = None
    session_title: Optional[str] = "Career Mentorship"


class ChatRequest(BaseSchema):
    content: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class ChatResponse(BaseSchema):
    id: str
    role: str = "assistant"
    content: str
    created_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}


# ============================================================
# O*NET DATA SCHEMAS
# ============================================================

class OnetOccupation(BaseSchema):
    onet_code: str
    title: str
    description: Optional[str] = None
    job_zone: Optional[int] = None
    bright_outlook: Optional[bool] = False
    green_economy: Optional[bool] = False
    median_annual_wage: Optional[int] = None
    employment_estimate: Optional[int] = None
    typical_education: Optional[str] = None
    work_experience: Optional[str] = None
    on_job_training: Optional[str] = None
    sample_jobs: Optional[List[str]] = []


class OnetSkill(BaseSchema):
    id: Optional[str] = None
    onet_code: str
    skill_name: str
    skill_id: Optional[str] = None
    importance: Optional[float] = 0.0
    level: Optional[float] = 0.0
    skill_category: Optional[str] = None


class OnetSearchResult(BaseSchema):
    onet_code: str
    title: str
    description: Optional[str] = None
    job_zone: Optional[int] = None
    bright_outlook: Optional[bool] = False
    median_annual_wage: Optional[int] = None


# ============================================================
# AGENT EVENTS & PROGRESS
# ============================================================

class AgentEvent(BaseSchema):
    agent_name: str
    status: str
    message: str
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ProgressStats(BaseSchema):
    total_tasks: int = 0
    completed_tasks: int = 0
    completion_percentage: float = 0.0
    hours_spent: float = 0.0
    estimated_hours_remaining: float = 0.0
    active_stage: Optional[int] = None
    milestones_achieved: int = 0
    total_milestones: int = 0
