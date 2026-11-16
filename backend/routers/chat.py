"""PathPilot AI — Chat Router (AI Career Assistant)"""
import logging
from fastapi import APIRouter, HTTPException, Body
from db.supabase import get_supabase
from config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

SYSTEM_PROMPT = """You are PathPilot AI, an expert career guidance assistant.
You have access to the student's profile, skills, and career roadmap.
Be encouraging, specific, and actionable. Format responses with markdown (bold, bullets, code blocks).
Always reference specific skills, stages, or courses from the student's roadmap when relevant.
Keep responses concise but informative (200-400 words max unless detail is needed)."""


def _build_context(user_id: str, sb) -> str:
    """Build context string from student profile + roadmap."""
    profile_r = sb.table("profiles").select("*").eq("id", user_id).maybe_single().execute()
    skills_r = sb.table("student_skills").select("skill_name,proficiency_level,skill_category")\
        .eq("user_id", user_id).limit(20).execute()
    roadmap_r = sb.table("roadmaps").select("target_career,completion_percentage,total_duration_months")\
        .eq("user_id", user_id).eq("is_primary", True).maybe_single().execute()

    profile = profile_r.data or {}
    skills = skills_r.data or []
    roadmap = roadmap_r.data or {}

    skill_list = ", ".join(f"{s['skill_name']} (lvl {s['proficiency_level']})" for s in skills[:10])
    context = f"""
STUDENT PROFILE:
- Name: {profile.get('full_name', 'Student')}
- Education: {profile.get('education_level', 'bachelor')} in {profile.get('specialization', 'unknown')}
- Weekly study hours: {profile.get('weekly_hours', 10)}h/week
- Career goals: {profile.get('career_goals', 'Not specified')}
- Current skills: {skill_list}

ACTIVE ROADMAP:
- Target career: {roadmap.get('target_career', 'Not selected')}
- Overall progress: {roadmap.get('completion_percentage', 0):.0f}%
- Duration: {roadmap.get('total_duration_months', 12)} months
"""
    return context.strip()


@router.get("/chat/{user_id}/sessions")
def get_sessions(user_id: str):
    sb = get_supabase()
    r = sb.table("chat_sessions").select("*").eq("user_id", user_id)\
        .order("created_at", desc=True).limit(20).execute()
    return r.data or []


@router.post("/chat/{user_id}/sessions", status_code=201)
def create_session(user_id: str, data: dict = Body(default={})):
    sb = get_supabase()
    r = sb.table("chat_sessions").insert({
        "user_id": user_id,
        "session_title": data.get("title", "New Conversation"),
    }).execute()
    return r.data[0] if r.data else {}


@router.get("/chat/sessions/{session_id}/messages")
def get_messages(session_id: str):
    sb = get_supabase()
    r = sb.table("chat_messages").select("*").eq("session_id", session_id)\
        .order("created_at").execute()
    return r.data or []


@router.post("/chat/sessions/{session_id}/message")
def send_message(session_id: str, data: dict = Body(...)):
    """Send a message and get AI response."""
    content = data.get("content", "").strip()
    if not content:
        raise HTTPException(400, "content required")

    sb = get_supabase()

    # Get session to find user_id
    session_r = sb.table("chat_sessions").select("*").eq("id", session_id).maybe_single().execute()
    if not session_r.data:
        raise HTTPException(404, "Session not found")
    user_id = session_r.data["user_id"]

    # Save user message
    user_msg_r = sb.table("chat_messages").insert({
        "session_id": session_id,
        "role": "user",
        "content": content,
    }).execute()

    # Fetch conversation history (last 10 messages)
    history_r = sb.table("chat_messages").select("role,content")\
        .eq("session_id", session_id).order("created_at").limit(10).execute()
    history = history_r.data or []

    # Build context
    student_context = _build_context(user_id, sb)

    if not settings.gemini_api_key:
        ai_content = (
            f"I'm PathPilot AI! I see you're asking: **\"{content}\"**\n\n"
            "To get real AI responses, please configure your `GEMINI_API_KEY` in the `.env` file.\n\n"
            "Once configured, I'll be able to:\n"
            "- Analyze your skill gaps in detail\n"
            "- Suggest next learning steps from your roadmap\n"
            "- Recommend specific projects for your career goal\n"
            "- Answer any career guidance questions!"
        )
    else:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            # Build conversation for Gemini
            chat_history = []
            for msg in history[:-1]:  # exclude latest user message (we'll send separately)
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append({"role": role, "parts": [msg["content"]]})

            full_prompt = f"{SYSTEM_PROMPT}\n\n{student_context}\n\nStudent question: {content}"
            response = model.generate_content(full_prompt)
            ai_content = response.text

        except Exception as e:
            logger.error(f"Gemini chat error: {e}")
            ai_content = "I encountered an error processing your request. Please try again."

    # Save AI response
    ai_msg_r = sb.table("chat_messages").insert({
        "session_id": session_id,
        "role": "assistant",
        "content": ai_content,
    }).execute()

    # Update session title if first message
    if len(history) <= 1:
        title = content[:50] + ("..." if len(content) > 50 else "")
        sb.table("chat_sessions").update({"session_title": title}).eq("id", session_id).execute()

    return {
        "id": ai_msg_r.data[0]["id"] if ai_msg_r.data else "",
        "role": "assistant",
        "content": ai_content,
        "created_at": ai_msg_r.data[0]["created_at"] if ai_msg_r.data else "",
    }
