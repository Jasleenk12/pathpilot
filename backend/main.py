"""PathPilot AI — FastAPI Application Entrypoint"""
import logging
import google.generativeai as genai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routers import profile, careers, roadmap, chat, onet, progress

# ── Settings ───────────────────────────────────────────────────────────────────
settings = get_settings()
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)

# ── Initialise Gemini ──────────────────────────────────────────────────────────
if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)
    logger.info("Gemini API configured ✓")
else:
    logger.warning("GEMINI_API_KEY not set — AI features will use fallback mock data")

# ── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="PathPilot AI API",
    description=(
        "Agentic Career Roadmap Generator — powered by Gemini + LangGraph + O*NET.\n\n"
        "Uses O*NET data under license from USDOL/ETA. O*NET® is a trademark of USDOL/ETA."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ───────────────────────────────────────────────────────────────────────
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(profile.router, prefix="/api", tags=["Profile"])
app.include_router(careers.router, prefix="/api", tags=["Careers"])
app.include_router(roadmap.router, prefix="/api", tags=["Roadmap"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(onet.router, prefix="/api", tags=["O*NET"])
app.include_router(progress.router, prefix="/api", tags=["Progress"])


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "gemini_configured": bool(settings.gemini_api_key),
        "supabase_configured": bool(settings.supabase_url and settings.supabase_service_role_key),
        "environment": settings.app_env,
    }


@app.get("/", tags=["System"])
def root():
    return {
        "app": "PathPilot AI",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.__dict__.get("backend_host", "0.0.0.0"),
        port=int(settings.__dict__.get("backend_port", 8000)),
        reload=settings.app_env == "development",
    )
