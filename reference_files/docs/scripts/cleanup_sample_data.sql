-- URGENT: Clean up sample data that was incorrectly applied to real user profile
-- User's real UUID: b0934595-c30d-450c-8713-acefe807a831
-- Sample data was meant for: 09f94574-1817-454f-b123-deccdecc8dac

-- 1. Remove the sample project_overview data from real user
DELETE FROM "public"."project_overview" 
WHERE "user_id" = 'b0934595-c30d-450c-8713-acefe807a831'
AND "project_name" = 'AI-Powered Creative Writing Assistant'
AND "project_type" = 'Technology/Writing';

-- 2. Remove any sample project_updates that might have been created
DELETE FROM "public"."project_updates"
WHERE "user_id" = 'b0934595-c30d-450c-8713-acefe807a831'
AND "project_id" IN (
    SELECT "id" FROM "public"."project_overview" 
    WHERE "project_name" = 'AI-Powered Creative Writing Assistant'
);

-- 3. Remove any sample conversations for the test UUID (if they exist)
DELETE FROM "public"."conversations"
WHERE "user_id" = '09f94574-1817-454f-b123-deccdecc8dac';

-- 4. Remove any sample project data for the test UUID
DELETE FROM "public"."project_overview"
WHERE "user_id" = '09f94574-1817-454f-b123-deccdecc8dac';

DELETE FROM "public"."project_updates"
WHERE "user_id" = '09f94574-1817-454f-b123-deccdecc8dac';

-- 5. Check for orphaned conversations (conversations without valid creator_profiles)
-- This will help us find your missing conversations
SELECT 
    c.id,
    c.user_id,
    c.created_at,
    c.message_text,
    cp.id as profile_exists
FROM conversations c
LEFT JOIN creator_profiles cp ON c.user_id = cp.id
WHERE cp.id IS NULL
ORDER BY c.created_at DESC
LIMIT 20;

-- 6. Verify your real profile still exists
SELECT id, first_name, last_name, slack_email, created_at
FROM creator_profiles 
WHERE id = 'b0934595-c30d-450c-8713-acefe807a831'; 