-- WingmanMatch Database Schema Verification Script
-- File: verify_wm_schema.sql
-- Description: Comprehensive verification of fresh WingmanMatch database schema
-- Usage: Run after creating fresh WingmanMatch database with all tables and functions
-- 
-- This script verifies:
-- 1. All required tables exist with correct columns and types
-- 2. All specified indexes are present
-- 3. haversine_miles function works correctly
-- 4. Table constraints and foreign keys are properly configured
-- 5. Row Level Security policies are in place

\echo '========================================='
\echo 'WingmanMatch Database Schema Verification'
\echo '========================================='
\echo ''

-- Initialize verification tracking
DO $$
DECLARE
    verification_count INTEGER := 0;
    failure_count INTEGER := 0;
    total_tests INTEGER := 0;
BEGIN
    -- Track test execution
    total_tests := 50; -- Update this as we add more tests
    
    \echo 'Starting comprehensive schema verification...'
    \echo ''
END $$;

-- ===========================================
-- 1. TABLE EXISTENCE VERIFICATION
-- ===========================================

\echo '1. VERIFYING TABLE EXISTENCE'
\echo '----------------------------'

-- Check core WingmanMatch tables
DO $$
DECLARE
    table_exists BOOLEAN;
    table_name TEXT;
    tables_to_check TEXT[] := ARRAY['user_locations', 'wingman_matches', 'approach_challenges', 'wingman_sessions'];
    t TEXT;
BEGIN
    FOREACH t IN ARRAY tables_to_check
    LOOP
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = t
        ) INTO table_exists;
        
        IF table_exists THEN
            RAISE NOTICE '✅ Table "%" exists', t;
        ELSE
            RAISE NOTICE '❌ MISSING TABLE: "%"', t;
        END IF;
    END LOOP;
END $$;

-- Check fresh WingmanMatch core tables
DO $$
DECLARE
    table_exists BOOLEAN;
    fresh_tables TEXT[] := ARRAY['user_profiles', 'dating_goals', 'confidence_test_results'];
    t TEXT;
BEGIN
    FOREACH t IN ARRAY fresh_tables
    LOOP
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = t
        ) INTO table_exists;
        
        IF table_exists THEN
            RAISE NOTICE '✅ Fresh table "%" exists', t;
        ELSE
            RAISE NOTICE '❌ MISSING FRESH TABLE: "%"', t;
        END IF;
    END LOOP;
END $$;

\echo ''

-- ===========================================
-- 2. COLUMN STRUCTURE VERIFICATION  
-- ===========================================

\echo '2. VERIFYING COLUMN STRUCTURES'
\echo '-------------------------------'

-- Verify user_locations table structure
DO $$
DECLARE
    column_count INTEGER;
    expected_columns TEXT[] := ARRAY['user_id', 'lat', 'lng', 'city', 'max_travel_miles', 'updated_at'];
    col TEXT;
    col_exists BOOLEAN;
BEGIN
    RAISE NOTICE 'Checking user_locations table structure:';
    
    FOREACH col IN ARRAY expected_columns
    LOOP
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'user_locations'
            AND column_name = col
        ) INTO col_exists;
        
        IF col_exists THEN
            RAISE NOTICE '  ✅ Column "%" exists', col;
        ELSE
            RAISE NOTICE '  ❌ MISSING COLUMN: "%"', col;
        END IF;
    END LOOP;
END $$;

-- Verify wingman_matches table structure
DO $$
DECLARE
    expected_columns TEXT[] := ARRAY['id', 'user1_id', 'user2_id', 'status', 'user1_reputation', 'user2_reputation', 'created_at'];
    col TEXT;
    col_exists BOOLEAN;
BEGIN
    RAISE NOTICE 'Checking wingman_matches table structure:';
    
    FOREACH col IN ARRAY expected_columns
    LOOP
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'wingman_matches'
            AND column_name = col
        ) INTO col_exists;
        
        IF col_exists THEN
            RAISE NOTICE '  ✅ Column "%" exists', col;
        ELSE
            RAISE NOTICE '  ❌ MISSING COLUMN: "%"', col;
        END IF;
    END LOOP;
END $$;

-- Verify approach_challenges table structure
DO $$
DECLARE
    expected_columns TEXT[] := ARRAY['id', 'difficulty', 'title', 'description', 'points', 'created_at'];
    col TEXT;
    col_exists BOOLEAN;
BEGIN
    RAISE NOTICE 'Checking approach_challenges table structure:';
    
    FOREACH col IN ARRAY expected_columns
    LOOP
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'approach_challenges'
            AND column_name = col
        ) INTO col_exists;
        
        IF col_exists THEN
            RAISE NOTICE '  ✅ Column "%" exists', col;
        ELSE
            RAISE NOTICE '  ❌ MISSING COLUMN: "%"', col;
        END IF;
    END LOOP;
END $$;

-- Verify wingman_sessions table structure
DO $$
DECLARE
    expected_columns TEXT[] := ARRAY['id', 'match_id', 'user1_challenge_id', 'user2_challenge_id', 'venue_name', 'scheduled_time', 'status', 'completed_at', 'user1_completed_confirmed_by_user2', 'user2_completed_confirmed_by_user1', 'notes', 'created_at'];
    col TEXT;
    col_exists BOOLEAN;
BEGIN
    RAISE NOTICE 'Checking wingman_sessions table structure:';
    
    FOREACH col IN ARRAY expected_columns
    LOOP
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'wingman_sessions'
            AND column_name = col
        ) INTO col_exists;
        
        IF col_exists THEN
            RAISE NOTICE '  ✅ Column "%" exists', col;
        ELSE
            RAISE NOTICE '  ❌ MISSING COLUMN: "%"', col;
        END IF;
    END LOOP;
END $$;

-- Verify user_profiles table structure
DO $$
DECLARE
    expected_columns TEXT[] := ARRAY['id', 'name', 'age', 'bio', 'interests', 'photos', 'height', 'occupation', 'education', 'relationship_goals', 'deal_breakers', 'created_at', 'updated_at'];
    col TEXT;
    col_exists BOOLEAN;
BEGIN
    RAISE NOTICE 'Checking user_profiles table structure:';
    
    FOREACH col IN ARRAY expected_columns
    LOOP
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'user_profiles'
            AND column_name = col
        ) INTO col_exists;
        
        IF col_exists THEN
            RAISE NOTICE '  ✅ Column "%" exists', col;
        ELSE
            RAISE NOTICE '  ❌ MISSING COLUMN: "%"', col;
        END IF;
    END LOOP;
END $$;

-- Verify dating_goals table structure
DO $$
DECLARE
    expected_columns TEXT[] := ARRAY['id', 'user_id', 'relationship_type', 'timeline', 'priorities', 'deal_breakers', 'preferred_age_range', 'location_preference', 'lifestyle_preferences', 'created_at', 'updated_at'];
    col TEXT;
    col_exists BOOLEAN;
BEGIN
    RAISE NOTICE 'Checking dating_goals table structure:';
    
    FOREACH col IN ARRAY expected_columns
    LOOP
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'dating_goals'
            AND column_name = col
        ) INTO col_exists;
        
        IF col_exists THEN
            RAISE NOTICE '  ✅ Column "%" exists', col;
        ELSE
            RAISE NOTICE '  ❌ MISSING COLUMN: "%"', col;
        END IF;
    END LOOP;
END $$;

-- Verify confidence_test_results table structure
DO $$
DECLARE
    expected_columns TEXT[] := ARRAY['id', 'user_id', 'test_type', 'responses', 'scores', 'archetype', 'recommendations', 'completed_at'];
    col TEXT;
    col_exists BOOLEAN;
BEGIN
    RAISE NOTICE 'Checking confidence_test_results table structure:';
    
    FOREACH col IN ARRAY expected_columns
    LOOP
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'confidence_test_results'
            AND column_name = col
        ) INTO col_exists;
        
        IF col_exists THEN
            RAISE NOTICE '  ✅ Column "%" exists', col;
        ELSE
            RAISE NOTICE '  ❌ MISSING COLUMN: "%"', col;
        END IF;
    END LOOP;
END $$;

\echo ''

-- ===========================================
-- 3. DATA TYPE VERIFICATION
-- ===========================================

\echo '3. VERIFYING COLUMN DATA TYPES'
\echo '------------------------------'

-- Check critical data types
DO $$
DECLARE
    rec RECORD;
    type_correct BOOLEAN := true;
BEGIN
    RAISE NOTICE 'Checking critical column data types:';
    
    -- Check user_locations coordinate types
    SELECT data_type INTO rec FROM information_schema.columns 
    WHERE table_schema = 'public' AND table_name = 'user_locations' AND column_name = 'lat';
    
    IF rec.data_type = 'numeric' THEN
        RAISE NOTICE '  ✅ user_locations.lat has correct type (numeric)';
    ELSE
        RAISE NOTICE '  ❌ user_locations.lat has wrong type: % (expected: numeric)', rec.data_type;
        type_correct := false;
    END IF;
    
    -- Check UUID columns
    SELECT data_type INTO rec FROM information_schema.columns 
    WHERE table_schema = 'public' AND table_name = 'wingman_matches' AND column_name = 'id';
    
    IF rec.data_type = 'uuid' THEN
        RAISE NOTICE '  ✅ wingman_matches.id has correct type (uuid)';
    ELSE
        RAISE NOTICE '  ❌ wingman_matches.id has wrong type: % (expected: uuid)', rec.data_type;
        type_correct := false;
    END IF;
    
    -- Check timestamp columns
    SELECT data_type INTO rec FROM information_schema.columns 
    WHERE table_schema = 'public' AND table_name = 'wingman_sessions' AND column_name = 'created_at';
    
    IF rec.data_type = 'timestamp with time zone' THEN
        RAISE NOTICE '  ✅ wingman_sessions.created_at has correct type (timestamp with time zone)';
    ELSE
        RAISE NOTICE '  ❌ wingman_sessions.created_at has wrong type: % (expected: timestamp with time zone)', rec.data_type;
        type_correct := false;
    END IF;
    
    IF type_correct THEN
        RAISE NOTICE '  ✅ All critical data types verified successfully';
    END IF;
END $$;

\echo ''

-- ===========================================
-- 4. INDEX VERIFICATION
-- ===========================================

\echo '4. VERIFYING INDEXES'
\echo '--------------------'

-- Check all required indexes
DO $$
DECLARE
    index_exists BOOLEAN;
    expected_indexes TEXT[] := ARRAY[
        'idx_user_locations_user_id',
        'idx_user_locations_lat_lng', 
        'idx_user_locations_city',
        'idx_wingman_matches_user1',
        'idx_wingman_matches_user2',
        'idx_wingman_matches_status',
        'idx_wingman_matches_created_at',
        'idx_approach_challenges_difficulty',
        'idx_wingman_sessions_match_id',
        'idx_wingman_sessions_status',
        'idx_wingman_sessions_scheduled_time',
        'idx_user_profiles_age',
        'idx_user_profiles_relationship_goals',
        'idx_dating_goals_user_id',
        'idx_dating_goals_relationship_type',
        'idx_confidence_test_results_user_id',
        'idx_confidence_test_results_archetype'
    ];
    idx TEXT;
BEGIN
    FOREACH idx IN ARRAY expected_indexes
    LOOP
        SELECT EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND indexname = idx
        ) INTO index_exists;
        
        IF index_exists THEN
            RAISE NOTICE '✅ Index "%" exists', idx;
        ELSE
            RAISE NOTICE '❌ MISSING INDEX: "%"', idx;
        END IF;
    END LOOP;
END $$;

\echo ''

-- ===========================================
-- 5. FUNCTION VERIFICATION
-- ===========================================

\echo '5. VERIFYING HAVERSINE_MILES FUNCTION'
\echo '--------------------------------------'

-- Test haversine_miles function existence and functionality
DO $$
DECLARE
    func_exists BOOLEAN;
    test_distance NUMERIC;
    expected_distance NUMERIC := 0.1; -- Expected ~0.1 miles between very close points
    tolerance NUMERIC := 0.05; -- 5% tolerance
BEGIN
    -- Check function exists
    SELECT EXISTS (
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid 
        WHERE n.nspname = 'public' 
        AND p.proname = 'haversine_miles'
    ) INTO func_exists;
    
    IF func_exists THEN
        RAISE NOTICE '✅ haversine_miles function exists';
        
        -- Test function with known coordinates (very close points in San Francisco)
        -- Coordinates approximately 0.1 miles apart
        SELECT public.haversine_miles(
            37.7749,   -- SF latitude 1
            -122.4194, -- SF longitude 1  
            37.7759,   -- SF latitude 2 (slightly north)
            -122.4184  -- SF longitude 2 (slightly east)
        ) INTO test_distance;
        
        RAISE NOTICE '  Distance calculation test: %.4f miles', test_distance;
        
        -- Verify distance is reasonable (should be around 0.1 miles)
        IF test_distance BETWEEN 0.05 AND 0.15 THEN
            RAISE NOTICE '  ✅ Function returns reasonable distance for close coordinates';
        ELSE
            RAISE NOTICE '  ❌ Function returns unreasonable distance: %.4f miles (expected ~0.1)', test_distance;
        END IF;
        
        -- Test function with identical coordinates (should return 0)
        SELECT public.haversine_miles(37.7749, -122.4194, 37.7749, -122.4194) INTO test_distance;
        
        IF test_distance = 0 THEN
            RAISE NOTICE '  ✅ Function correctly returns 0 for identical coordinates';
        ELSE
            RAISE NOTICE '  ❌ Function returns %.4f for identical coordinates (expected 0)', test_distance;
        END IF;
        
    ELSE
        RAISE NOTICE '❌ haversine_miles function MISSING';
    END IF;
END $$;

\echo ''

-- ===========================================
-- 6. CONSTRAINT VERIFICATION
-- ===========================================

\echo '6. VERIFYING TABLE CONSTRAINTS'
\echo '------------------------------'

-- Check primary key constraints
DO $$
DECLARE
    constraint_exists BOOLEAN;
    expected_pks TEXT[][] := ARRAY[
        ['user_locations', 'user_locations_pkey'],
        ['wingman_matches', 'wingman_matches_pkey'],
        ['approach_challenges', 'approach_challenges_pkey'],
        ['wingman_sessions', 'wingman_sessions_pkey'],
        ['user_profiles', 'user_profiles_pkey'],
        ['dating_goals', 'dating_goals_pkey'],
        ['confidence_test_results', 'confidence_test_results_pkey']
    ];
    pk_pair TEXT[];
BEGIN
    RAISE NOTICE 'Checking primary key constraints:';
    
    FOREACH pk_pair SLICE 1 IN ARRAY expected_pks
    LOOP
        SELECT EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_schema = 'public' 
            AND table_name = pk_pair[1]
            AND constraint_name = pk_pair[2]
            AND constraint_type = 'PRIMARY KEY'
        ) INTO constraint_exists;
        
        IF constraint_exists THEN
            RAISE NOTICE '  ✅ Primary key "%" exists on table "%"', pk_pair[2], pk_pair[1];
        ELSE
            RAISE NOTICE '  ❌ MISSING PRIMARY KEY: "%" on table "%"', pk_pair[2], pk_pair[1];
        END IF;
    END LOOP;
END $$;

-- Check foreign key constraints
DO $$
DECLARE
    constraint_exists BOOLEAN;
    expected_fks TEXT[][] := ARRAY[
        ['user_locations', 'user_locations_user_id_fkey'],
        ['wingman_matches', 'wingman_matches_user1_id_fkey'],
        ['wingman_matches', 'wingman_matches_user2_id_fkey'],
        ['wingman_sessions', 'wingman_sessions_match_id_fkey'],
        ['wingman_sessions', 'wingman_sessions_user1_challenge_fkey'],
        ['wingman_sessions', 'wingman_sessions_user2_challenge_fkey'],
        ['dating_goals', 'dating_goals_user_id_fkey'],
        ['confidence_test_results', 'confidence_test_results_user_id_fkey']
    ];
    fk_pair TEXT[];
BEGIN
    RAISE NOTICE 'Checking foreign key constraints:';
    
    FOREACH fk_pair SLICE 1 IN ARRAY expected_fks
    LOOP
        SELECT EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_schema = 'public' 
            AND table_name = fk_pair[1]
            AND constraint_name = fk_pair[2]
            AND constraint_type = 'FOREIGN KEY'
        ) INTO constraint_exists;
        
        IF constraint_exists THEN
            RAISE NOTICE '  ✅ Foreign key "%" exists on table "%"', fk_pair[2], fk_pair[1];
        ELSE
            RAISE NOTICE '  ❌ MISSING FOREIGN KEY: "%" on table "%"', fk_pair[2], fk_pair[1];
        END IF;
    END LOOP;
END $$;

-- Check check constraints
DO $$
DECLARE
    constraint_exists BOOLEAN;
    expected_checks TEXT[][] := ARRAY[
        ['wingman_matches', 'wingman_matches_different_users'],
        ['approach_challenges', 'approach_challenges_difficulty_check'],
        ['wingman_sessions', 'wingman_sessions_status_check']
    ];
    check_pair TEXT[];
BEGIN
    RAISE NOTICE 'Checking check constraints:';
    
    FOREACH check_pair SLICE 1 IN ARRAY expected_checks
    LOOP
        SELECT EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_schema = 'public' 
            AND table_name = check_pair[1]
            AND constraint_name = check_pair[2]
            AND constraint_type = 'CHECK'
        ) INTO constraint_exists;
        
        IF constraint_exists THEN
            RAISE NOTICE '  ✅ Check constraint "%" exists on table "%"', check_pair[2], check_pair[1];
        ELSE
            RAISE NOTICE '  ❌ MISSING CHECK CONSTRAINT: "%" on table "%"', check_pair[2], check_pair[1];
        END IF;
    END LOOP;
END $$;

\echo ''

-- ===========================================
-- 7. ROW LEVEL SECURITY VERIFICATION
-- ===========================================

\echo '7. VERIFYING ROW LEVEL SECURITY'
\echo '--------------------------------'

-- Check RLS is enabled on tables
DO $$
DECLARE
    rls_enabled BOOLEAN;
    tables_with_rls TEXT[] := ARRAY['user_locations', 'wingman_matches', 'approach_challenges', 'wingman_sessions', 'user_profiles', 'dating_goals', 'confidence_test_results'];
    tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY tables_with_rls
    LOOP
        SELECT relrowsecurity INTO rls_enabled
        FROM pg_class 
        WHERE relname = tbl AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public');
        
        IF rls_enabled THEN
            RAISE NOTICE '✅ RLS enabled on table "%"', tbl;
        ELSE
            RAISE NOTICE '❌ RLS NOT ENABLED on table "%"', tbl;
        END IF;
    END LOOP;
END $$;

-- Check specific RLS policies exist
DO $$
DECLARE
    policy_exists BOOLEAN;
    expected_policies TEXT[][] := ARRAY[
        ['user_locations', 'Users can view their own location'],
        ['user_locations', 'Users can insert their own location'],
        ['user_locations', 'Users can update their own location'],
        ['wingman_matches', 'Users can view their own matches'],
        ['wingman_matches', 'Users can create matches involving themselves'],
        ['wingman_matches', 'Users can update their own matches'],
        ['approach_challenges', 'Anyone can view challenges'],
        ['wingman_sessions', 'Users can view sessions for their matches'],
        ['wingman_sessions', 'Users can create sessions for their matches'],
        ['wingman_sessions', 'Users can update sessions for their matches'],
        ['user_profiles', 'Users can view all profiles'],
        ['user_profiles', 'Users can insert their own profile'],
        ['user_profiles', 'Users can update their own profile'],
        ['dating_goals', 'Users can view their own dating goals'],
        ['dating_goals', 'Users can insert their own dating goals'],
        ['dating_goals', 'Users can update their own dating goals'],
        ['confidence_test_results', 'Users can view their own test results'],
        ['confidence_test_results', 'Users can insert their own test results'],
        ['confidence_test_results', 'Users can update their own test results']
    ];
    policy_pair TEXT[];
BEGIN
    RAISE NOTICE 'Checking RLS policies:';
    
    FOREACH policy_pair SLICE 1 IN ARRAY expected_policies
    LOOP
        SELECT EXISTS (
            SELECT 1 FROM pg_policies 
            WHERE schemaname = 'public' 
            AND tablename = policy_pair[1]
            AND policyname = policy_pair[2]
        ) INTO policy_exists;
        
        IF policy_exists THEN
            RAISE NOTICE '  ✅ Policy "%" exists on table "%"', policy_pair[2], policy_pair[1];
        ELSE
            RAISE NOTICE '  ❌ MISSING POLICY: "%" on table "%"', policy_pair[2], policy_pair[1];
        END IF;
    END LOOP;
END $$;

\echo ''

-- ===========================================
-- 8. SAMPLE DATA VERIFICATION (if present)
-- ===========================================

\echo '8. VERIFYING SAMPLE DATA'
\echo '------------------------'

-- Check if approach_challenges has been seeded
DO $$
DECLARE
    challenge_count INTEGER;
    beginner_count INTEGER;
    intermediate_count INTEGER;
    advanced_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO challenge_count FROM approach_challenges;
    
    IF challenge_count > 0 THEN
        RAISE NOTICE '✅ approach_challenges table has data (% records)', challenge_count;
        
        -- Check distribution by difficulty
        SELECT COUNT(*) INTO beginner_count FROM approach_challenges WHERE difficulty = 'beginner';
        SELECT COUNT(*) INTO intermediate_count FROM approach_challenges WHERE difficulty = 'intermediate';
        SELECT COUNT(*) INTO advanced_count FROM approach_challenges WHERE difficulty = 'advanced';
        
        RAISE NOTICE '  • Beginner challenges: %', beginner_count;
        RAISE NOTICE '  • Intermediate challenges: %', intermediate_count;
        RAISE NOTICE '  • Advanced challenges: %', advanced_count;
        
        IF beginner_count >= 3 AND intermediate_count >= 3 AND advanced_count >= 3 THEN
            RAISE NOTICE '  ✅ Good distribution of challenges across all difficulty levels';
        ELSE
            RAISE NOTICE '  ⚠️  Consider adding more challenges (recommend at least 3 per difficulty)';
        END IF;
    ELSE
        RAISE NOTICE '⚠️  approach_challenges table is empty (run seed_challenges.sql to populate)';
    END IF;
END $$;

\echo ''

-- ===========================================
-- 9. FUNCTIONAL VERIFICATION
-- ===========================================

\echo '9. PERFORMING FUNCTIONAL TESTS'
\echo '-------------------------------'

-- Test that we can perform basic operations (without actually inserting data)
DO $$
DECLARE
    query_works BOOLEAN := true;
BEGIN
    RAISE NOTICE 'Testing basic query functionality:';
    
    -- Test we can query each table structure
    BEGIN
        PERFORM 1 FROM user_locations WHERE false; -- Doesn't return data but tests query structure
        RAISE NOTICE '  ✅ user_locations table is queryable';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '  ❌ Error querying user_locations: %', SQLERRM;
        query_works := false;
    END;
    
    BEGIN
        PERFORM 1 FROM wingman_matches WHERE false;
        RAISE NOTICE '  ✅ wingman_matches table is queryable';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '  ❌ Error querying wingman_matches: %', SQLERRM;
        query_works := false;
    END;
    
    BEGIN
        PERFORM 1 FROM approach_challenges WHERE false;
        RAISE NOTICE '  ✅ approach_challenges table is queryable';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '  ❌ Error querying approach_challenges: %', SQLERRM;
        query_works := false;
    END;
    
    BEGIN
        PERFORM 1 FROM wingman_sessions WHERE false;
        RAISE NOTICE '  ✅ wingman_sessions table is queryable';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '  ❌ Error querying wingman_sessions: %', SQLERRM;
        query_works := false;
    END;
    
    BEGIN
        PERFORM 1 FROM user_profiles WHERE false;
        RAISE NOTICE '  ✅ user_profiles table is queryable';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '  ❌ Error querying user_profiles: %', SQLERRM;
        query_works := false;
    END;
    
    BEGIN
        PERFORM 1 FROM dating_goals WHERE false;
        RAISE NOTICE '  ✅ dating_goals table is queryable';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '  ❌ Error querying dating_goals: %', SQLERRM;
        query_works := false;
    END;
    
    BEGIN
        PERFORM 1 FROM confidence_test_results WHERE false;
        RAISE NOTICE '  ✅ confidence_test_results table is queryable';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '  ❌ Error querying confidence_test_results: %', SQLERRM;
        query_works := false;
    END;
    
    IF query_works THEN
        RAISE NOTICE '  ✅ All tables are functional for basic queries';
    END IF;
END $$;

\echo ''

-- ===========================================
-- 10. SUMMARY REPORT
-- ===========================================

\echo '10. VERIFICATION SUMMARY'
\echo '========================'

-- Generate final summary
DO $$
DECLARE
    core_table_count INTEGER;
    fresh_table_count INTEGER;
    index_count INTEGER;
    constraint_count INTEGER;
    function_exists BOOLEAN;
    rls_count INTEGER;
    overall_status TEXT;
BEGIN
    -- Count verified components
    SELECT COUNT(*) INTO core_table_count 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('user_locations', 'wingman_matches', 'approach_challenges', 'wingman_sessions');
    
    SELECT COUNT(*) INTO fresh_table_count 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('user_profiles', 'dating_goals', 'confidence_test_results');
    
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND (indexname LIKE 'idx_%locations_%' 
       OR indexname LIKE 'idx_%matches_%'
       OR indexname LIKE 'idx_%challenges_%'
       OR indexname LIKE 'idx_%sessions_%'
       OR indexname LIKE 'idx_%profiles_%'
       OR indexname LIKE 'idx_%goals_%'
       OR indexname LIKE 'idx_%results_%');
    
    SELECT COUNT(*) INTO constraint_count
    FROM information_schema.table_constraints 
    WHERE constraint_schema = 'public' 
    AND table_name IN ('user_locations', 'wingman_matches', 'approach_challenges', 'wingman_sessions', 'user_profiles', 'dating_goals', 'confidence_test_results')
    AND constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY', 'CHECK');
    
    SELECT EXISTS (
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid 
        WHERE n.nspname = 'public' 
        AND p.proname = 'haversine_miles'
    ) INTO function_exists;
    
    SELECT COUNT(*) INTO rls_count
    FROM pg_class 
    WHERE relname IN ('user_locations', 'wingman_matches', 'approach_challenges', 'wingman_sessions', 'user_profiles', 'dating_goals', 'confidence_test_results')
    AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
    AND relrowsecurity = true;
    
    RAISE NOTICE '';
    RAISE NOTICE 'VERIFICATION RESULTS:';
    RAISE NOTICE '====================';
    RAISE NOTICE '';
    RAISE NOTICE 'Core WingmanMatch Tables: %/4 (%)', core_table_count, 
        CASE WHEN core_table_count = 4 THEN '✅ PASS' ELSE '❌ FAIL' END;
    RAISE NOTICE 'Fresh Core Tables: %/3 (%)', fresh_table_count,
        CASE WHEN fresh_table_count = 3 THEN '✅ PASS' ELSE '❌ FAIL' END;
    RAISE NOTICE 'Performance Indexes: %/17 (%)', index_count,
        CASE WHEN index_count >= 15 THEN '✅ PASS' ELSE '❌ FAIL' END;
    RAISE NOTICE 'Table Constraints: %+ (%)', constraint_count,
        CASE WHEN constraint_count >= 12 THEN '✅ PASS' ELSE '❌ FAIL' END;
    RAISE NOTICE 'Haversine Function: %', 
        CASE WHEN function_exists THEN '✅ PASS' ELSE '❌ FAIL' END;
    RAISE NOTICE 'Row Level Security: %/7 (%)', rls_count,
        CASE WHEN rls_count = 7 THEN '✅ PASS' ELSE '❌ FAIL' END;
    
    RAISE NOTICE '';
    
    -- Overall status
    IF core_table_count = 4 AND fresh_table_count = 3 AND index_count >= 15 AND 
       constraint_count >= 12 AND function_exists AND rls_count = 7 THEN
        overall_status := '🎉 FRESH WINGMANMATCH DATABASE VERIFICATION SUCCESSFUL';
        RAISE NOTICE '%', overall_status;
        RAISE NOTICE 'Fresh WingmanMatch database is ready for the application!';
    ELSE
        overall_status := '⚠️  FRESH DATABASE VERIFICATION ISSUES DETECTED';
        RAISE NOTICE '%', overall_status;
        RAISE NOTICE 'Please review the failed checks above and create/fix the missing components.';
    END IF;
    
    RAISE NOTICE '';
    RAISE NOTICE 'Run this script again after making any fixes to re-verify.';
    RAISE NOTICE '';
END $$;

\echo '========================================='
\echo 'WingmanMatch Schema Verification Complete'
\echo '========================================='