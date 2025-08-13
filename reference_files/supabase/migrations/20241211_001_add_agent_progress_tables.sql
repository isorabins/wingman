-- Migration: Add agent progress tracking tables
-- Date: 2024-12-11
-- Purpose: Support Claude agents for creativity testing and project overview flows

-- Table for tracking creativity test progress (mid-flow saves)
CREATE TABLE IF NOT EXISTS creativity_test_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES creator_profiles(id) ON DELETE CASCADE,
    flow_step INTEGER NOT NULL DEFAULT 1,
    current_responses JSONB DEFAULT '{}',
    flow_state JSONB DEFAULT '{}',
    last_question_asked TEXT,
    completion_percentage DECIMAL(5,2) DEFAULT 0.0,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for tracking project overview progress (mid-flow saves)  
CREATE TABLE IF NOT EXISTS project_overview_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES creator_profiles(id) ON DELETE CASCADE,
    flow_step INTEGER NOT NULL DEFAULT 1,
    current_data JSONB DEFAULT '{}',
    flow_state JSONB DEFAULT '{}',
    topic_progress JSONB DEFAULT '{}', -- Track "Topic X of 8" progress
    completion_percentage DECIMAL(5,2) DEFAULT 0.0,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for agent conversation context (lightweight session storage)
CREATE TABLE IF NOT EXISTS agent_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES creator_profiles(id) ON DELETE CASCADE,
    agent_type TEXT NOT NULL, -- 'creativity_test' or 'project_overview'
    thread_id TEXT NOT NULL,
    session_context JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '24 hours'),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_creativity_progress_user_id ON creativity_test_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_creativity_progress_completed ON creativity_test_progress(is_completed);
CREATE INDEX IF NOT EXISTS idx_project_progress_user_id ON project_overview_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_project_progress_completed ON project_overview_progress(is_completed);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_user_thread ON agent_sessions(user_id, thread_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_active ON agent_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_expires ON agent_sessions(expires_at);

-- Add updated_at triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_creativity_test_progress_updated_at BEFORE UPDATE ON creativity_test_progress 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_overview_progress_updated_at BEFORE UPDATE ON project_overview_progress 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_sessions_updated_at BEFORE UPDATE ON agent_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 