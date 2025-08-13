-- Migration: Add confidence_test_progress table for WingmanMatch
-- File: 002_add_confidence_test_progress.sql
-- Dependencies: 001_add_wingman_tables.sql
-- Description: Creates progress tracking table for confidence assessment flow

BEGIN;

-- Create confidence_test_progress table for tracking assessment progress
CREATE TABLE IF NOT EXISTS "public"."confidence_test_progress" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "flow_step" INTEGER NOT NULL DEFAULT 1,
    "current_responses" "jsonb" DEFAULT '{}'::jsonb,
    "flow_state" "jsonb" DEFAULT '{}'::jsonb,
    "last_question_asked" TEXT,
    "completion_percentage" DECIMAL(5,2) DEFAULT 0.0,
    "is_completed" BOOLEAN DEFAULT FALSE,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT "confidence_test_progress_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "confidence_test_progress_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."user_profiles"("id") ON DELETE CASCADE
);

-- Create agent_sessions table for tracking agent sessions
CREATE TABLE IF NOT EXISTS "public"."agent_sessions" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "agent_type" VARCHAR(50) NOT NULL,
    "thread_id" VARCHAR(200) NOT NULL,
    "session_context" "jsonb" DEFAULT '{}'::jsonb,
    "is_active" BOOLEAN DEFAULT TRUE,
    "expires_at" TIMESTAMP WITH TIME ZONE,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT "agent_sessions_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "agent_sessions_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."user_profiles"("id") ON DELETE CASCADE
);

-- Create indexes for performance optimization

-- Confidence test progress indexes
CREATE INDEX IF NOT EXISTS "idx_confidence_test_progress_user_id" ON "public"."confidence_test_progress"("user_id");
CREATE INDEX IF NOT EXISTS "idx_confidence_test_progress_is_completed" ON "public"."confidence_test_progress"("is_completed");
CREATE INDEX IF NOT EXISTS "idx_confidence_test_progress_updated_at" ON "public"."confidence_test_progress"("updated_at");

-- Agent sessions indexes
CREATE INDEX IF NOT EXISTS "idx_agent_sessions_user_id" ON "public"."agent_sessions"("user_id");
CREATE INDEX IF NOT EXISTS "idx_agent_sessions_agent_type" ON "public"."agent_sessions"("agent_type");
CREATE INDEX IF NOT EXISTS "idx_agent_sessions_thread_id" ON "public"."agent_sessions"("thread_id");
CREATE INDEX IF NOT EXISTS "idx_agent_sessions_is_active" ON "public"."agent_sessions"("is_active");
CREATE INDEX IF NOT EXISTS "idx_agent_sessions_expires_at" ON "public"."agent_sessions"("expires_at");

-- Enable Row Level Security on new tables
ALTER TABLE "public"."confidence_test_progress" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."agent_sessions" ENABLE ROW LEVEL SECURITY;

-- RLS Policies for confidence_test_progress
CREATE POLICY "Users can view their own test progress" ON "public"."confidence_test_progress"
    FOR SELECT TO authenticated
    USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can insert their own test progress" ON "public"."confidence_test_progress"
    FOR INSERT TO authenticated
    WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update their own test progress" ON "public"."confidence_test_progress"
    FOR UPDATE TO authenticated
    USING ((SELECT auth.uid()) = user_id)
    WITH CHECK ((SELECT auth.uid()) = user_id);

-- RLS Policies for agent_sessions
CREATE POLICY "Users can view their own agent sessions" ON "public"."agent_sessions"
    FOR SELECT TO authenticated
    USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can insert their own agent sessions" ON "public"."agent_sessions"
    FOR INSERT TO authenticated
    WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update their own agent sessions" ON "public"."agent_sessions"
    FOR UPDATE TO authenticated
    USING ((SELECT auth.uid()) = user_id)
    WITH CHECK ((SELECT auth.uid()) = user_id);

COMMIT;