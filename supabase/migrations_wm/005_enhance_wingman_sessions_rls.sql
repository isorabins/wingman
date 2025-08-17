-- Migration: Enhance wingman_sessions RLS policies
-- File: 005_enhance_wingman_sessions_rls.sql
-- Date: 2025-08-16
-- Purpose: Add DELETE policy and optimize existing RLS policies for wingman_sessions
-- Dependencies: 001_add_wingman_tables.sql (wingman_sessions table exists)

BEGIN;

-- Add optimized index for RLS policy performance
-- This index supports the common pattern of looking up sessions by match_id
-- and checking match participants, improving RLS policy query performance
CREATE INDEX IF NOT EXISTS "idx_wingman_sessions_match_participants" 
ON "public"."wingman_sessions"("match_id") 
INCLUDE ("id", "status", "created_at");

-- Add comprehensive index for session management queries
-- Supports efficient queries for session status and scheduling
CREATE INDEX IF NOT EXISTS "idx_wingman_sessions_status_time" 
ON "public"."wingman_sessions"("status", "scheduled_time") 
WHERE "status" IN ('scheduled', 'in_progress');

-- Add DELETE policy (service role only)
-- This ensures only admin operations can delete sessions
-- Regular users cannot delete sessions for data integrity and audit purposes
CREATE POLICY "Only service role can delete sessions" ON "public"."wingman_sessions"
    FOR DELETE TO service_role
    USING (true);

-- Add explicit DENY policy for authenticated users trying to delete
-- This provides clear security enforcement and error messaging
CREATE POLICY "Authenticated users cannot delete sessions" ON "public"."wingman_sessions"
    FOR DELETE TO authenticated
    USING (false);

-- Add policy comments for documentation and maintainability
COMMENT ON POLICY "Users can view sessions for their matches" ON "public"."wingman_sessions" 
IS 'Participants can view sessions for matches they are part of - joins with wingman_matches to verify user1_id or user2_id equals auth.uid()';

COMMENT ON POLICY "Users can create sessions for their matches" ON "public"."wingman_sessions" 
IS 'Participants can create sessions only for matches they are part of - API handles additional validation';

COMMENT ON POLICY "Users can update sessions for their matches" ON "public"."wingman_sessions" 
IS 'Participants can update session details like confirmations, notes, and status for their matches only';

COMMENT ON POLICY "Only service role can delete sessions" ON "public"."wingman_sessions" 
IS 'Admin/service role exclusive deletion for data integrity and audit trail preservation';

COMMENT ON POLICY "Authenticated users cannot delete sessions" ON "public"."wingman_sessions" 
IS 'Explicit denial for regular user deletion attempts - provides clear security boundary';

-- Add table comment documenting the security model
COMMENT ON TABLE "public"."wingman_sessions" 
IS 'Wingman buddy sessions with RLS policies ensuring participant-only access. DELETE restricted to service role for data integrity.';

-- Add column comments for clarity on security-sensitive fields
COMMENT ON COLUMN "public"."wingman_sessions"."match_id" 
IS 'Foreign key to wingman_matches - used by RLS policies to determine participant access rights';

COMMENT ON COLUMN "public"."wingman_sessions"."status" 
IS 'Session status: scheduled, in_progress, completed, cancelled, no_show - indexed for performance';

-- Verify RLS is enabled (should already be enabled from 001_add_wingman_tables.sql)
-- This is idempotent and safe to run multiple times
ALTER TABLE "public"."wingman_sessions" ENABLE ROW LEVEL SECURITY;

COMMIT;