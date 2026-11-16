-- ============================================================
-- PathPilot AI — Database Schema Migration 001
-- Run this in your Supabase SQL editor or via psql
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================
-- USER PROFILES
-- ============================================================

CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    degree TEXT,                    -- e.g. "Bachelor of Technology"
    specialization TEXT,            -- e.g. "Computer Science"
    education_level TEXT CHECK (education_level IN (
        'high_school', 'associate', 'bachelor', 'master', 'phd', 'bootcamp', 'self_taught'
    )),
    graduation_year INTEGER,
    university TEXT,
    weekly_hours INTEGER DEFAULT 10,        -- Available learning hours per week
    roadmap_duration_months INTEGER DEFAULT 12,
    preferred_roles TEXT[],                  -- ["Data Scientist", "ML Engineer"]
    career_goals TEXT,
    linkedin_url TEXT,
    github_url TEXT,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS student_interests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    interest TEXT NOT NULL,
    interest_type TEXT CHECK (interest_type IN ('domain', 'industry', 'technology', 'activity')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS student_skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    skill_category TEXT CHECK (skill_category IN ('technical', 'soft', 'tool', 'language', 'framework', 'other')),
    proficiency_level INTEGER CHECK (proficiency_level BETWEEN 1 AND 5),
    -- 1=Beginner, 2=Elementary, 3=Intermediate, 4=Advanced, 5=Expert
    years_experience FLOAT,
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS student_experience (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    experience_type TEXT CHECK (experience_type IN ('project', 'internship', 'job', 'freelance', 'research', 'course')),
    title TEXT NOT NULL,
    organization TEXT,
    description TEXT,
    technologies_used TEXT[],
    start_date DATE,
    end_date DATE,
    is_ongoing BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- O*NET OCCUPATIONAL DATA
-- ============================================================

CREATE TABLE IF NOT EXISTS onet_occupations (
    onet_code TEXT PRIMARY KEY,          -- e.g. "15-2051.00"
    title TEXT NOT NULL,
    description TEXT,
    job_zone INTEGER CHECK (job_zone BETWEEN 1 AND 5),
    -- 1=Little prep, 5=Extensive prep
    bright_outlook BOOLEAN DEFAULT FALSE,
    green_economy BOOLEAN DEFAULT FALSE,
    median_annual_wage INTEGER,
    employment_estimate INTEGER,
    typical_education TEXT,
    work_experience TEXT,
    on_job_training TEXT,
    sample_jobs TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS onet_skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    onet_code TEXT NOT NULL REFERENCES onet_occupations(onet_code) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    skill_id TEXT,                       -- O*NET internal skill element ID
    importance FLOAT,                    -- 0-100
    level FLOAT,                         -- 0-7 (O*NET scale)
    skill_category TEXT CHECK (skill_category IN ('basic', 'cross_functional', 'technical')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS onet_knowledge (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    onet_code TEXT NOT NULL REFERENCES onet_occupations(onet_code) ON DELETE CASCADE,
    knowledge_area TEXT NOT NULL,
    knowledge_id TEXT,
    importance FLOAT,
    level FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS onet_abilities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    onet_code TEXT NOT NULL REFERENCES onet_occupations(onet_code) ON DELETE CASCADE,
    ability_name TEXT NOT NULL,
    ability_id TEXT,
    importance FLOAT,
    level FLOAT,
    ability_category TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS onet_interests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    onet_code TEXT NOT NULL REFERENCES onet_occupations(onet_code) ON DELETE CASCADE,
    interest_area TEXT NOT NULL,          -- Holland Code: Realistic, Investigative, etc.
    score FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS onet_technology (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    onet_code TEXT NOT NULL REFERENCES onet_occupations(onet_code) ON DELETE CASCADE,
    technology_name TEXT NOT NULL,
    technology_category TEXT,
    is_hot_technology BOOLEAN DEFAULT FALSE,
    is_in_demand BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS onet_work_activities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    onet_code TEXT NOT NULL REFERENCES onet_occupations(onet_code) ON DELETE CASCADE,
    activity_name TEXT NOT NULL,
    activity_id TEXT,
    importance FLOAT,
    level FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- CAREER RECOMMENDATIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS career_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    onet_code TEXT REFERENCES onet_occupations(onet_code),
    career_title TEXT NOT NULL,
    suitability_score FLOAT CHECK (suitability_score BETWEEN 0 AND 100),
    match_explanation TEXT,
    matching_skills TEXT[],
    missing_skills TEXT[],
    is_selected BOOLEAN DEFAULT FALSE,
    generation_version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ROADMAPS
-- ============================================================

CREATE TABLE IF NOT EXISTS roadmaps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    career_recommendation_id UUID REFERENCES career_recommendations(id),
    onet_code TEXT REFERENCES onet_occupations(onet_code),
    target_career TEXT NOT NULL,
    total_duration_months INTEGER,
    weekly_hours INTEGER,
    status TEXT CHECK (status IN ('generating', 'active', 'completed', 'archived')) DEFAULT 'generating',
    completion_percentage FLOAT DEFAULT 0,
    is_primary BOOLEAN DEFAULT TRUE,
    generation_version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS roadmap_stages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    roadmap_id UUID NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
    stage_number INTEGER NOT NULL,
    stage_title TEXT NOT NULL,
    stage_description TEXT,
    skills_to_learn TEXT[],
    prerequisites TEXT[],
    duration_weeks INTEGER,
    status TEXT CHECK (status IN ('locked', 'in_progress', 'completed')) DEFAULT 'locked',
    completion_percentage FLOAT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS roadmap_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stage_id UUID NOT NULL REFERENCES roadmap_stages(id) ON DELETE CASCADE,
    task_type TEXT CHECK (task_type IN ('course', 'project', 'reading', 'certification', 'practice', 'milestone')),
    title TEXT NOT NULL,
    description TEXT,
    url TEXT,
    platform TEXT,                       -- e.g. "Coursera", "YouTube", "Udemy"
    duration_hours INTEGER,
    difficulty TEXT CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
    skills_covered TEXT[],
    is_required BOOLEAN DEFAULT TRUE,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMPTZ,
    source TEXT CHECK (source IN ('onet', 'ai_recommended', 'sample')) DEFAULT 'ai_recommended',
    -- Clearly label data source
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS milestones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    roadmap_id UUID NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
    stage_id UUID REFERENCES roadmap_stages(id),
    title TEXT NOT NULL,
    description TEXT,
    milestone_type TEXT CHECK (milestone_type IN ('skill', 'project', 'certification', 'interview_ready', 'job_ready')),
    is_achieved BOOLEAN DEFAULT FALSE,
    achieved_at TIMESTAMPTZ,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- SKILL GAP ANALYSIS
-- ============================================================

CREATE TABLE IF NOT EXISTS skill_gap_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    roadmap_id UUID REFERENCES roadmaps(id) ON DELETE CASCADE,
    onet_code TEXT REFERENCES onet_occupations(onet_code),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS skill_gap_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID NOT NULL REFERENCES skill_gap_analyses(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    student_level FLOAT,                 -- 0-5 (student proficiency)
    required_level FLOAT,               -- 0-7 (O*NET scale, normalized)
    gap_category TEXT CHECK (gap_category IN ('acquired', 'needs_improvement', 'must_learn')),
    onet_importance FLOAT,
    priority INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- CHAT / AI ASSISTANT
-- ============================================================

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    roadmap_id UUID REFERENCES roadmaps(id),
    session_title TEXT DEFAULT 'New Conversation',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role TEXT CHECK (role IN ('user', 'assistant', 'system')) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',          -- e.g. {"sources": [], "onet_codes": []}
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- AGENT EXECUTION LOGS
-- ============================================================

CREATE TABLE IF NOT EXISTS agent_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    roadmap_id UUID REFERENCES roadmaps(id),
    session_id TEXT NOT NULL,            -- LangGraph execution session
    agent_name TEXT NOT NULL,
    status TEXT CHECK (status IN ('started', 'running', 'completed', 'failed', 'skipped')),
    message TEXT,
    metadata JSONB DEFAULT '{}',
    duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_student_skills_user ON student_skills(user_id);
CREATE INDEX IF NOT EXISTS idx_student_interests_user ON student_interests(user_id);
CREATE INDEX IF NOT EXISTS idx_onet_skills_code ON onet_skills(onet_code);
CREATE INDEX IF NOT EXISTS idx_onet_skills_name ON onet_skills USING gin(to_tsvector('english', skill_name));
CREATE INDEX IF NOT EXISTS idx_onet_occupations_title ON onet_occupations USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_career_recommendations_user ON career_recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_roadmaps_user ON roadmaps(user_id);
CREATE INDEX IF NOT EXISTS idx_roadmap_stages_roadmap ON roadmap_stages(roadmap_id);
CREATE INDEX IF NOT EXISTS idx_roadmap_tasks_stage ON roadmap_tasks(stage_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_user ON agent_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_session ON agent_logs(session_id);

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_interests ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_experience ENABLE ROW LEVEL SECURITY;
ALTER TABLE career_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE roadmaps ENABLE ROW LEVEL SECURITY;
ALTER TABLE roadmap_stages ENABLE ROW LEVEL SECURITY;
ALTER TABLE roadmap_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE milestones ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_gap_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_gap_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_logs ENABLE ROW LEVEL SECURITY;

-- Users can only access their own data
CREATE POLICY "Users own their profile" ON profiles FOR ALL USING (auth.uid() = id);
CREATE POLICY "Users own their interests" ON student_interests FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users own their skills" ON student_skills FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users own their experience" ON student_experience FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users own career recs" ON career_recommendations FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users own roadmaps" ON roadmaps FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users own roadmap stages" ON roadmap_stages FOR ALL USING (
    roadmap_id IN (SELECT id FROM roadmaps WHERE user_id = auth.uid())
);
CREATE POLICY "Users own roadmap tasks" ON roadmap_tasks FOR ALL USING (
    stage_id IN (
        SELECT s.id FROM roadmap_stages s
        JOIN roadmaps r ON s.roadmap_id = r.id
        WHERE r.user_id = auth.uid()
    )
);
CREATE POLICY "Users own milestones" ON milestones FOR ALL USING (
    roadmap_id IN (SELECT id FROM roadmaps WHERE user_id = auth.uid())
);
CREATE POLICY "Users own skill gaps" ON skill_gap_analyses FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users own skill gap items" ON skill_gap_items FOR ALL USING (
    analysis_id IN (SELECT id FROM skill_gap_analyses WHERE user_id = auth.uid())
);
CREATE POLICY "Users own chat sessions" ON chat_sessions FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users own chat messages" ON chat_messages FOR ALL USING (
    session_id IN (SELECT id FROM chat_sessions WHERE user_id = auth.uid())
);
CREATE POLICY "Users own agent logs" ON agent_logs FOR ALL USING (auth.uid() = user_id);

-- O*NET tables are publicly readable (no auth needed)
ALTER TABLE onet_occupations ENABLE ROW LEVEL SECURITY;
ALTER TABLE onet_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE onet_knowledge ENABLE ROW LEVEL SECURITY;
ALTER TABLE onet_abilities ENABLE ROW LEVEL SECURITY;
ALTER TABLE onet_interests ENABLE ROW LEVEL SECURITY;
ALTER TABLE onet_technology ENABLE ROW LEVEL SECURITY;
ALTER TABLE onet_work_activities ENABLE ROW LEVEL SECURITY;

CREATE POLICY "O*NET data is public read" ON onet_occupations FOR SELECT USING (true);
CREATE POLICY "O*NET skills public read" ON onet_skills FOR SELECT USING (true);
CREATE POLICY "O*NET knowledge public read" ON onet_knowledge FOR SELECT USING (true);
CREATE POLICY "O*NET abilities public read" ON onet_abilities FOR SELECT USING (true);
CREATE POLICY "O*NET interests public read" ON onet_interests FOR SELECT USING (true);
CREATE POLICY "O*NET technology public read" ON onet_technology FOR SELECT USING (true);
CREATE POLICY "O*NET work activities public read" ON onet_work_activities FOR SELECT USING (true);

-- Service role bypass for backend inserts
CREATE POLICY "Service role full access profiles" ON profiles FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role onet write" ON onet_occupations FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role onet skills write" ON onet_skills FOR ALL USING (auth.role() = 'service_role');

-- ============================================================
-- UPDATED_AT TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER roadmaps_updated_at BEFORE UPDATE ON roadmaps
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER chat_sessions_updated_at BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
