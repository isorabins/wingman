-- Migration: Create WingmanMatch database tables
-- File: 001_add_wingman_tables.sql
-- Dependencies: None
-- Description: Creates all core tables for WingmanMatch fresh database
--              Includes user_profiles, user_locations, wingman_matches, approach_challenges, wingman_sessions
--              Includes indexes and haversine_miles function for distance calculations

BEGIN;

-- Create user_profiles table (fresh WingmanMatch users)
CREATE TABLE IF NOT EXISTS "public"."user_profiles" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "email" "text",
    "first_name" "text",
    "last_name" "text", 
    "bio" "text",
    "photo_url" "text",
    "experience_level" VARCHAR(50) DEFAULT 'beginner',
    "confidence_archetype" "text",
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT "user_profiles_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "user_profiles_experience_level_check" CHECK ("experience_level" IN ('beginner', 'intermediate', 'advanced'))
);

-- Create dating_goals table (WingmanMatch goals instead of project_overview)
CREATE TABLE IF NOT EXISTS "public"."dating_goals" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "goals" "text",
    "preferred_venues" "text"[],
    "comfort_level" VARCHAR(50) DEFAULT 'moderate',
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT "dating_goals_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "dating_goals_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."user_profiles"("id") ON DELETE CASCADE
);

-- Create confidence_test_results table (WingmanMatch confidence assessment)
CREATE TABLE IF NOT EXISTS "public"."confidence_test_results" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "test_responses" "jsonb" DEFAULT '{}'::jsonb,
    "archetype_scores" "jsonb" DEFAULT '{}'::jsonb,
    "assigned_archetype" "text",
    "experience_level" VARCHAR(50),
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT "confidence_test_results_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "confidence_test_results_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."user_profiles"("id") ON DELETE CASCADE
);

-- Create user_locations table for geographic matching
CREATE TABLE IF NOT EXISTS "public"."user_locations" (
    "user_id" "uuid" NOT NULL,
    "lat" DECIMAL(10,8) NOT NULL,
    "lng" DECIMAL(11,8) NOT NULL,
    "city" VARCHAR(100),
    "max_travel_miles" INTEGER DEFAULT 20,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT "user_locations_pkey" PRIMARY KEY ("user_id"),
    CONSTRAINT "user_locations_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."user_profiles"("id") ON DELETE CASCADE
);

-- Create wingman_matches table for buddy matching
CREATE TABLE IF NOT EXISTS "public"."wingman_matches" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user1_id" "uuid" NOT NULL,
    "user2_id" "uuid" NOT NULL,
    "status" VARCHAR(50) DEFAULT 'pending',
    "user1_reputation" INTEGER DEFAULT 0,
    "user2_reputation" INTEGER DEFAULT 0,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT "wingman_matches_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "wingman_matches_user1_id_fkey" FOREIGN KEY ("user1_id") REFERENCES "public"."user_profiles"("id") ON DELETE CASCADE,
    CONSTRAINT "wingman_matches_user2_id_fkey" FOREIGN KEY ("user2_id") REFERENCES "public"."user_profiles"("id") ON DELETE CASCADE,
    CONSTRAINT "wingman_matches_different_users" CHECK ("user1_id" != "user2_id")
);

-- Create approach_challenges table for difficulty-based challenges
CREATE TABLE IF NOT EXISTS "public"."approach_challenges" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "difficulty" VARCHAR(50) NOT NULL,
    "title" VARCHAR(200) NOT NULL,
    "description" TEXT,
    "points" INTEGER DEFAULT 10,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT "approach_challenges_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "approach_challenges_difficulty_check" CHECK ("difficulty" IN ('beginner', 'intermediate', 'advanced'))
);

-- Create wingman_sessions table for tracking buddy sessions
CREATE TABLE IF NOT EXISTS "public"."wingman_sessions" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "match_id" "uuid" NOT NULL,
    "user1_challenge_id" "uuid",
    "user2_challenge_id" "uuid", 
    "venue_name" VARCHAR(200),
    "scheduled_time" TIMESTAMP WITH TIME ZONE,
    "status" VARCHAR(50) DEFAULT 'scheduled',
    "completed_at" TIMESTAMP WITH TIME ZONE,
    "user1_completed_confirmed_by_user2" BOOLEAN DEFAULT FALSE,
    "user2_completed_confirmed_by_user1" BOOLEAN DEFAULT FALSE,
    "notes" TEXT,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT "wingman_sessions_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "wingman_sessions_match_id_fkey" FOREIGN KEY ("match_id") REFERENCES "public"."wingman_matches"("id") ON DELETE CASCADE,
    CONSTRAINT "wingman_sessions_user1_challenge_fkey" FOREIGN KEY ("user1_challenge_id") REFERENCES "public"."approach_challenges"("id"),
    CONSTRAINT "wingman_sessions_user2_challenge_fkey" FOREIGN KEY ("user2_challenge_id") REFERENCES "public"."approach_challenges"("id"),
    CONSTRAINT "wingman_sessions_status_check" CHECK ("status" IN ('scheduled', 'in_progress', 'completed', 'cancelled', 'no_show'))
);

-- Create indexes for performance optimization

-- User profile indexes
CREATE INDEX IF NOT EXISTS "idx_user_profiles_email" ON "public"."user_profiles"("email");
CREATE INDEX IF NOT EXISTS "idx_user_profiles_experience_level" ON "public"."user_profiles"("experience_level");
CREATE INDEX IF NOT EXISTS "idx_user_profiles_confidence_archetype" ON "public"."user_profiles"("confidence_archetype");

-- Dating goals indexes  
CREATE INDEX IF NOT EXISTS "idx_dating_goals_user_id" ON "public"."dating_goals"("user_id");

-- Confidence test results indexes
CREATE INDEX IF NOT EXISTS "idx_confidence_test_results_user_id" ON "public"."confidence_test_results"("user_id");
CREATE INDEX IF NOT EXISTS "idx_confidence_test_results_archetype" ON "public"."confidence_test_results"("assigned_archetype");

-- User location indexes
CREATE INDEX IF NOT EXISTS "idx_user_locations_user_id" ON "public"."user_locations"("user_id");
CREATE INDEX IF NOT EXISTS "idx_user_locations_lat_lng" ON "public"."user_locations"("lat", "lng");
CREATE INDEX IF NOT EXISTS "idx_user_locations_city" ON "public"."user_locations"("city");

-- Wingman match indexes
CREATE INDEX IF NOT EXISTS "idx_wingman_matches_user1" ON "public"."wingman_matches"("user1_id");
CREATE INDEX IF NOT EXISTS "idx_wingman_matches_user2" ON "public"."wingman_matches"("user2_id");
CREATE INDEX IF NOT EXISTS "idx_wingman_matches_status" ON "public"."wingman_matches"("status");
CREATE INDEX IF NOT EXISTS "idx_wingman_matches_created_at" ON "public"."wingman_matches"("created_at");

-- Approach challenge indexes
CREATE INDEX IF NOT EXISTS "idx_approach_challenges_difficulty" ON "public"."approach_challenges"("difficulty");

-- Wingman session indexes
CREATE INDEX IF NOT EXISTS "idx_wingman_sessions_match_id" ON "public"."wingman_sessions"("match_id");
CREATE INDEX IF NOT EXISTS "idx_wingman_sessions_status" ON "public"."wingman_sessions"("status");
CREATE INDEX IF NOT EXISTS "idx_wingman_sessions_scheduled_time" ON "public"."wingman_sessions"("scheduled_time");

-- Create haversine_miles function for distance calculations
-- Returns distance between two points in miles using the Haversine formula
CREATE OR REPLACE FUNCTION "public"."haversine_miles"(
    "lat1" DECIMAL,
    "lng1" DECIMAL, 
    "lat2" DECIMAL,
    "lng2" DECIMAL
) RETURNS NUMERIC
LANGUAGE "plpgsql"
AS $$
DECLARE
    R CONSTANT NUMERIC := 3959; -- Earth's radius in miles
    dlat NUMERIC;
    dlng NUMERIC; 
    a NUMERIC;
    c NUMERIC;
BEGIN
    -- Convert degrees to radians
    dlat := RADIANS(lat2 - lat1);
    dlng := RADIANS(lng2 - lng1);
    
    -- Haversine formula
    a := SIN(dlat/2) * SIN(dlat/2) + 
         COS(RADIANS(lat1)) * COS(RADIANS(lat2)) * 
         SIN(dlng/2) * SIN(dlng/2);
    
    c := 2 * ATAN2(SQRT(a), SQRT(1-a));
    
    -- Return distance in miles
    RETURN R * c;
END;
$$;

-- Set function ownership
ALTER FUNCTION "public"."haversine_miles"(DECIMAL, DECIMAL, DECIMAL, DECIMAL) OWNER TO "postgres";

-- Enable Row Level Security on all tables
ALTER TABLE "public"."user_profiles" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."dating_goals" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."confidence_test_results" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."user_locations" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."wingman_matches" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."approach_challenges" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."wingman_sessions" ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_profiles
CREATE POLICY "Users can view their own profile" ON "public"."user_profiles"
    FOR SELECT TO authenticated
    USING ((SELECT auth.uid()) = id);

CREATE POLICY "Users can update their own profile" ON "public"."user_profiles"
    FOR UPDATE TO authenticated
    USING ((SELECT auth.uid()) = id)
    WITH CHECK ((SELECT auth.uid()) = id);

CREATE POLICY "Users can insert their own profile" ON "public"."user_profiles"
    FOR INSERT TO authenticated
    WITH CHECK ((SELECT auth.uid()) = id);

-- RLS Policies for dating_goals
CREATE POLICY "Users can view their own dating goals" ON "public"."dating_goals"
    FOR SELECT TO authenticated
    USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update their own dating goals" ON "public"."dating_goals"
    FOR UPDATE TO authenticated
    USING ((SELECT auth.uid()) = user_id)
    WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can insert their own dating goals" ON "public"."dating_goals"
    FOR INSERT TO authenticated
    WITH CHECK ((SELECT auth.uid()) = user_id);

-- RLS Policies for confidence_test_results
CREATE POLICY "Users can view their own test results" ON "public"."confidence_test_results"
    FOR SELECT TO authenticated
    USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can insert their own test results" ON "public"."confidence_test_results"
    FOR INSERT TO authenticated
    WITH CHECK ((SELECT auth.uid()) = user_id);

-- RLS Policies for user_locations
CREATE POLICY "Users can view their own location" ON "public"."user_locations"
    FOR SELECT TO authenticated
    USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can insert their own location" ON "public"."user_locations"
    FOR INSERT TO authenticated
    WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update their own location" ON "public"."user_locations"
    FOR UPDATE TO authenticated
    USING ((SELECT auth.uid()) = user_id)
    WITH CHECK ((SELECT auth.uid()) = user_id);

-- RLS Policies for wingman_matches
CREATE POLICY "Users can view their own matches" ON "public"."wingman_matches"
    FOR SELECT TO authenticated
    USING ((SELECT auth.uid()) IN (user1_id, user2_id));

CREATE POLICY "Users can create matches involving themselves" ON "public"."wingman_matches"
    FOR INSERT TO authenticated
    WITH CHECK ((SELECT auth.uid()) IN (user1_id, user2_id));

CREATE POLICY "Users can update their own matches" ON "public"."wingman_matches"
    FOR UPDATE TO authenticated
    USING ((SELECT auth.uid()) IN (user1_id, user2_id))
    WITH CHECK ((SELECT auth.uid()) IN (user1_id, user2_id));

-- RLS Policies for approach_challenges (public read access)
CREATE POLICY "Anyone can view challenges" ON "public"."approach_challenges"
    FOR SELECT TO authenticated, anon
    USING (true);

-- RLS Policies for wingman_sessions
CREATE POLICY "Users can view sessions for their matches" ON "public"."wingman_sessions"
    FOR SELECT TO authenticated
    USING (
        (SELECT auth.uid()) IN (
            SELECT user1_id FROM wingman_matches WHERE id = match_id
            UNION
            SELECT user2_id FROM wingman_matches WHERE id = match_id
        )
    );

CREATE POLICY "Users can create sessions for their matches" ON "public"."wingman_sessions"
    FOR INSERT TO authenticated
    WITH CHECK (
        (SELECT auth.uid()) IN (
            SELECT user1_id FROM wingman_matches WHERE id = match_id
            UNION
            SELECT user2_id FROM wingman_matches WHERE id = match_id
        )
    );

CREATE POLICY "Users can update sessions for their matches" ON "public"."wingman_sessions"
    FOR UPDATE TO authenticated
    USING (
        (SELECT auth.uid()) IN (
            SELECT user1_id FROM wingman_matches WHERE id = match_id
            UNION
            SELECT user2_id FROM wingman_matches WHERE id = match_id
        )
    )
    WITH CHECK (
        (SELECT auth.uid()) IN (
            SELECT user1_id FROM wingman_matches WHERE id = match_id
            UNION
            SELECT user2_id FROM wingman_matches WHERE id = match_id
        )
    );

COMMIT;