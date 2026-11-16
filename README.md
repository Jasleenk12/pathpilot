# PathPilot AI 🧭

> **Your Interests. Your Skills. Your Career. One Intelligent Roadmap.**

An AI-powered career guidance platform that transforms a student's educational background, interests, and skills into a personalized, step-by-step career roadmap — powered by **Google Gemini**, **LangGraph**, and the **O\*NET occupational database**.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Database Setup (Supabase)](#database-setup)
- [O\*NET Data Setup](#onet-data-setup)
- [Running Locally](#running-locally)
- [Project Structure](#project-structure)
- [Multi-Agent Workflow](#multi-agent-workflow)
- [API Reference](#api-reference)
- [Sample Roadmaps](#sample-roadmaps)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

---

## Overview

PathPilot AI is a full-stack Agentic AI application that:

1. **Collects** a student's profile (education, skills, interests, experience, goals)
2. **Discovers** suitable careers from the O\*NET occupational database
3. **Analyzes** skill gaps between the student's current abilities and career requirements
4. **Generates** a personalized, sequential learning roadmap
5. **Recommends** specific courses, projects, and certifications
6. **Validates** the roadmap for completeness and correctness
7. **Tracks** progress as the student completes tasks

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PathPilot AI                             │
├─────────────────┬───────────────────────┬───────────────────┤
│   Frontend      │      Backend          │    Database       │
│   Next.js 14    │   FastAPI (Python)    │   Supabase        │
│   TypeScript    │   LangGraph Agents    │   PostgreSQL      │
│   Tailwind CSS  │   Gemini API          │   O*NET Data      │
│   Supabase Auth │   SSE Streaming       │   RLS Policies    │
└─────────────────┴───────────────────────┴───────────────────┘
```

### Multi-Agent LangGraph Workflow

```
Student Profile
      │
      ▼
┌─────────────────┐
│ Profile Analyzer│  → Normalizes skills, identifies interests (RIASEC)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Career Discovery │  → Searches O*NET, ranks 5 best-fit careers (Gemini)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Skill Gap      │  → Compares student skills vs O*NET requirements
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Learning Planner │  → Creates sequential stages (respects weekly hours)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Resource Recom.  │  → Courses, projects, certifications per stage
└────────┬────────┘
         │
         ▼
┌─────────────────┐    ✗ Invalid (retry ≤2)
│Roadmap Validator│ ──────────────────────────┐
└────────┬────────┘                           │
         │ ✓ Valid                            │
         ▼                                   ▼
   Save Roadmap                       Learning Planner
   to Database                        (re-plan with corrections)
```

All agents stream real-time events to the frontend via Server-Sent Events (SSE).

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Node.js | 20+ | Frontend |
| Python | 3.11+ | Backend |
| npm | 9+ | Package manager |
| pip | 23+ | Python packages |

**External Services Required:**
- [Supabase](https://supabase.com) account (free tier works)
- [Google AI Studio](https://aistudio.google.com) Gemini API key

---

## Quick Start

### 1. Clone and Setup

```bash
cd pathpilot-ai

# Copy environment file
cp .env.example .env
# → Edit .env with your API keys (see Configuration section)
```

### 2. Install Dependencies

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install --legacy-peer-deps
```

### 3. Set Up Database

Run the migration SQL files in your Supabase SQL editor:
1. Go to your Supabase project → SQL Editor
2. Run `backend/db/migrations/001_initial_schema.sql`
3. Run `backend/db/migrations/002_onet_sample_data.sql`

### 4. Start the Application

**Terminal 1 — Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Configuration

Edit `.env` with these values:

### Required Keys

| Variable | Where to Get It | Description |
|----------|----------------|-------------|
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com/app/apikey) | Powers all 6 AI agents |
| `SUPABASE_URL` | Supabase → Settings → API | Your project URL |
| `SUPABASE_ANON_KEY` | Supabase → Settings → API | Public anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Settings → API | Backend service key |
| `NEXT_PUBLIC_SUPABASE_URL` | Same as SUPABASE_URL | Exposed to frontend |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Same as SUPABASE_ANON_KEY | Exposed to frontend |

### Optional Keys

| Variable | Description |
|----------|-------------|
| `ONET_API_KEY` | O\*NET Web API (not required — bundled data included) |
| `DATABASE_URL` | Direct PostgreSQL URL (Supabase provides this) |

---

## Database Setup

### Using Supabase (Recommended)

1. Create a free account at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to **SQL Editor** in the left sidebar
4. Create a new query, paste the contents of `001_initial_schema.sql`, run it
5. Create another query, paste `002_onet_sample_data.sql`, run it
6. Copy your project URL and keys from **Settings → API**

### Using Local PostgreSQL (Development)

```bash
# Start local Postgres with Docker
docker compose up postgres -d

# Apply migrations
psql postgresql://postgres:postgres@localhost:5432/pathpilot \
  -f backend/db/migrations/001_initial_schema.sql \
  -f backend/db/migrations/002_onet_sample_data.sql
```

**Note:** When using local Postgres, Supabase Auth won't work. For local dev without auth, the app will use a test user mode.

---

## O\*NET Data Setup

### Bundled Sample Data (Default)
The file `backend/db/migrations/002_onet_sample_data.sql` contains pre-loaded data for **18 key occupations** including:
- Data Scientists (15-2051.00)
- Software Developers (15-1252.00)  
- Statisticians / Data Analysts (15-2041.00)
- Web Developers (15-1254.00)
- Information Security Analysts (15-1212.00)
- And 13 more...

This is sufficient for demonstration and testing.

### Full O\*NET Database Import

To import the complete O\*NET database (~1,000 occupations):

1. Download the database from [onetcenter.org/database.html](https://www.onetcenter.org/database.html)
   - Select: **O\*NET 29.0 Database** → Download All Files (ZIP)
2. Extract to `backend/data/onet/`
3. Run the ingestion script:

```bash
cd backend
python db/onet_loader.py --data-dir data/onet/ --env .env
```

This script reads the official CSV files and loads them into PostgreSQL.

> **Attribution:** This product uses O\*NET data under license from the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA). O\*NET® is a trademark of USDOL/ETA.

---

## Running Locally

### Development Mode (Recommended)

```bash
# Terminal 1
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2
cd frontend && npm run dev
```

### Docker Compose

```bash
# Start everything (requires Docker)
docker compose up

# Backend only
docker compose up backend postgres

# Stop all
docker compose down
```

### Without API Keys (Demo Mode)

If `GEMINI_API_KEY` is not set, the app will:
- Show a warning banner in the dashboard
- Use mock data for agent responses
- Sample roadmaps remain fully functional (no API key needed)

---

## Project Structure

```
pathpilot-ai/
├── frontend/                   # Next.js 14 (App Router)
│   └── src/
│       ├── app/
│       │   ├── page.tsx        # Landing page
│       │   ├── (auth)/         # Login, signup
│       │   ├── (dashboard)/    # Protected app
│       │   │   ├── dashboard/
│       │   │   ├── onboarding/
│       │   │   ├── career-discovery/
│       │   │   ├── roadmap/
│       │   │   ├── skill-gap/
│       │   │   ├── chat/
│       │   │   ├── progress/
│       │   │   └── onet-explorer/
│       │   └── samples/        # Public sample roadmaps
│       ├── components/
│       ├── lib/                # Supabase client, API helpers
│       └── types/
│
├── backend/                    # Python FastAPI
│   ├── main.py                 # App entrypoint
│   ├── config.py               # Settings (env vars)
│   ├── agents/                 # 6 LangGraph agents
│   │   ├── graph.py            # StateGraph workflow
│   │   ├── state.py            # Shared TypedDict state
│   │   ├── profile_analyzer.py
│   │   ├── career_discovery.py
│   │   ├── skill_gap.py
│   │   ├── learning_planner.py
│   │   ├── resource_recommender.py
│   │   └── roadmap_validator.py
│   ├── routers/                # FastAPI route handlers
│   │   ├── profile.py
│   │   ├── careers.py
│   │   ├── roadmap.py          # Includes SSE streaming
│   │   ├── chat.py
│   │   ├── onet.py
│   │   └── progress.py
│   ├── db/
│   │   ├── supabase.py         # Supabase client + helpers
│   │   └── migrations/         # SQL migration files
│   ├── models/
│   │   └── schemas.py          # Pydantic v2 schemas
│   └── requirements.txt
│
├── .env.example                # Environment variable template
├── docker-compose.yml          # Local Docker setup
└── README.md
```

---

## Multi-Agent Workflow

### Agent 1: Profile Analyzer
- **Input:** Raw student profile (skills, interests, experience, goals)
- **Process:** Normalizes skill names, identifies RIASEC Holland codes from interests, calculates experience level
- **Output:** Enriched profile with `normalized_skills`, `holland_codes`, `experience_level`, `profile_summary`

### Agent 2: Career Discovery Agent
- **Input:** Enriched profile
- **Process:** Queries O\*NET occupations from Supabase, calls Gemini to rank top 5 matches by skills/interests overlap
- **Output:** 5 career recommendations with suitability scores, match explanations, matching/missing skills
- **Data Source:** O\*NET OnLine (onetcenter.org)

### Agent 3: Skill Gap Analysis Agent
- **Input:** Selected career + student skills
- **Process:** Fetches O\*NET required skills, compares against student's proficiency levels
- **Output:** Skills categorized as: ✅ Acquired / 🔶 Needs Improvement / ❌ Must Learn

### Agent 4: Learning Path Planner
- **Input:** Ordered skill gaps + learning preferences (hours/week, duration)
- **Process:** Calls Gemini to create 5-9 sequential stages respecting time constraints
- **Output:** Ordered stages with skills, descriptions, durations, prerequisites

### Agent 5: Resource Recommender
- **Input:** Learning stages
- **Process:** For each stage, calls Gemini to recommend courses, projects, certifications
- **Output:** Resources mapped to stages (clearly labeled as AI-recommended)

### Agent 6: Roadmap Validator
- **Input:** Complete roadmap
- **Process:** Calls Gemini to audit for missing skills, bad sequencing, unrealistic durations
- **Output:** `{valid: bool, issues: [], corrections: [], quality_score: float}`
- If invalid and `retry_count < 2`: triggers re-planning with corrections

---

## API Reference

Base URL: `http://localhost:8000`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/profile/{user_id}` | Get student profile |
| PUT | `/api/profile/{user_id}/onboarding` | Submit onboarding |
| GET | `/api/careers/{user_id}/recommendations` | Get career matches |
| POST | `/api/careers/{user_id}/recommendations/generate` | Generate AI recommendations |
| POST | `/api/roadmap/generate` | Start roadmap generation |
| GET | `/api/roadmap/{roadmap_id}/stream` | SSE event stream |
| PUT | `/api/roadmap/{roadmap_id}/task/{task_id}/complete` | Mark task done |
| POST | `/api/chat/sessions/{session_id}/message` | AI chat message |
| GET | `/api/onet/search?q=...` | Search O\*NET occupations |
| GET | `/api/onet/occupation/{code}` | Occupation detail |
| GET | `/api/progress/{user_id}` | Progress stats |

Full interactive API docs at: `http://localhost:8000/docs`

---

## Sample Roadmaps

Three fully-populated sample roadmaps are available at `/samples` **without login**:

### 🤖 AI/ML Engineer (12 months)
- Student: CS background, Python basics, math interest
- Career: Data Scientists (O\*NET 15-2051.00) — 87% match
- Stages: Python → Math/Stats → ML → Deep Learning → NLP/LLMs → MLOps → Projects → Career Prep

### ⚙️ Backend Developer (10 months)
- Student: IT background, some programming
- Career: Software Developers (O\*NET 15-1252.00) — 91% match
- Stages: Programming → DSA → APIs → SQL → Frameworks → System Design → Docker/Cloud → Testing → Career Prep

### 📊 Data Analyst (8 months)
- Student: Commerce background, Excel skills
- Career: Statisticians (O\*NET 15-2041.00) — 83% match
- Stages: Excel → Statistics → SQL → Python → Power BI → Visualization → Projects → Career Prep

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key |
| `SUPABASE_URL` | ✅ Yes | Supabase project URL |
| `SUPABASE_ANON_KEY` | ✅ Yes | Supabase public key |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ Yes | Supabase service role key |
| `NEXT_PUBLIC_SUPABASE_URL` | ✅ Yes | Same as SUPABASE_URL (frontend) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | ✅ Yes | Same as SUPABASE_ANON_KEY (frontend) |
| `NEXT_PUBLIC_BACKEND_URL` | ⚠️ Optional | Backend URL (default: localhost:8000) |
| `DATABASE_URL` | ⚠️ Optional | PostgreSQL connection string |
| `JWT_SECRET` | ⚠️ Optional | JWT signing secret |
| `ONET_API_KEY` | ❌ No | O\*NET Web API (bundled data used instead) |

---

## Troubleshooting

### "Gemini API key not configured"
- Set `GEMINI_API_KEY` in your `.env` file
- Get a free key at [aistudio.google.com](https://aistudio.google.com/app/apikey)

### "Cannot connect to Supabase"
- Verify `SUPABASE_URL` and `SUPABASE_ANON_KEY` are correct
- Check your Supabase project is active (not paused)

### "O\*NET data not found"
- Run the migration files `001_initial_schema.sql` and `002_onet_sample_data.sql`
- For full data: run `python db/onet_loader.py`

### Frontend can't connect to backend
- Verify backend is running on port 8000: `curl http://localhost:8000/health`
- Set `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000` in `.env`

### TypeScript errors in frontend
```bash
cd frontend && npm run build
# Check error output for missing types
```

### Python import errors
```bash
cd backend
pip install -r requirements.txt --upgrade
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Auth | Supabase Auth |
| Backend | Python FastAPI, Uvicorn |
| AI Agents | LangGraph, Google Gemini (gemini-1.5-flash) |
| Database | Supabase (PostgreSQL) |
| Occupational Data | O\*NET OnLine (onetcenter.org) |
| Real-time | Server-Sent Events (SSE) |
| Charts | Recharts |
| PDF Export | react-to-print |

---

## Attribution

This product uses **O\*NET data** under license from the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA). O\*NET® is a trademark of USDOL/ETA.

Data sourced from: [O\*NET OnLine](https://www.onetcenter.org) — National Center for O\*NET Development.

---

## License

MIT License — See LICENSE file for details.

---

*Built with ❤️ for the LLM and Agentic AI Course Project*
