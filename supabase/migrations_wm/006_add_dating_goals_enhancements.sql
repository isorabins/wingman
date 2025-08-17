-- Migration: Enhance dating_goals table and add progress tracking
-- File: 006_add_dating_goals_enhancements.sql
-- Dependencies: 001_add_wingman_tables.sql
-- Description: Adds missing fields to dating_goals table and creates dating_goals_progress table

BEGIN;

-- Add missing fields to dating_goals table
ALTER TABLE "public"."dating_goals" 
ADD COLUMN IF NOT EXISTS "goals_data" "jsonb" DEFAULT '{}'::jsonb;

-- Create dating_goals_progress table for flow tracking
CREATE TABLE IF NOT EXISTS "public"."dating_goals_progress" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "flow_step" INTEGER DEFAULT 1,
    "current_data" "jsonb" DEFAULT '{}'::jsonb,
    "flow_state" "jsonb" DEFAULT '{}'::jsonb,
    "topic_progress" "jsonb" DEFAULT '{}'::jsonb,
    "completion_percentage" DECIMAL(5,2) DEFAULT 0.0,
    "is_completed" BOOLEAN DEFAULT FALSE,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT "dating_goals_progress_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "dating_goals_progress_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."user_profiles"("id") ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS "idx_dating_goals_progress_user_id" ON "public"."dating_goals_progress"("user_id");
CREATE INDEX IF NOT EXISTS "idx_dating_goals_progress_completion" ON "public"."dating_goals_progress"("is_completed");

-- Enable Row Level Security
ALTER TABLE "public"."dating_goals_progress" ENABLE ROW LEVEL SECURITY;

-- RLS Policies for dating_goals_progress
CREATE POLICY "Users can view their own dating goals progress" ON "public"."dating_goals_progress"
    FOR SELECT TO authenticated
    USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update their own dating goals progress" ON "public"."dating_goals_progress"
    FOR UPDATE TO authenticated
    USING ((SELECT auth.uid()) = user_id)
    WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can insert their own dating goals progress" ON "public"."dating_goals_progress"
    FOR INSERT TO authenticated
    WITH CHECK ((SELECT auth.uid()) = user_id);

COMMIT;