-- Seed Data: Approach Challenges for WingmanMatch
-- File: seed_challenges.sql
-- Description: Inserts realistic approach challenges for different difficulty levels
-- Usage: Run after 001_add_wingman_tables.sql migration

BEGIN;

-- Insert beginner level challenges
INSERT INTO "public"."approach_challenges" (
    "id",
    "difficulty", 
    "title",
    "description",
    "points"
) VALUES 
(
    'b1234567-1234-4321-b123-123456789001',
    'beginner',
    'Make eye contact with 5 people',
    'Practice making brief, friendly eye contact with 5 different people. A simple smile or nod is perfect. This builds confidence in non-verbal communication.',
    10
),
(
    'b1234567-1234-4321-b123-123456789002', 
    'beginner',
    'Say "good morning" to 3 strangers',
    'Greet 3 people you don''t know with a warm "good morning" or "hello". Choose safe, public spaces like coffee shops or bookstores.',
    10
),
(
    'b1234567-1234-4321-b123-123456789003',
    'beginner',
    'Ask someone for the time',
    'Ask a stranger for the time, even if you have your phone. This is a safe, low-pressure way to practice starting conversations with strangers.',
    15
)
ON CONFLICT (id) DO NOTHING;

-- Insert intermediate level challenges  
INSERT INTO "public"."approach_challenges" (
    "id",
    "difficulty",
    "title", 
    "description",
    "points"
) VALUES
(
    'i1234567-1234-4321-i123-123456789001',
    'intermediate',
    'Ask 3 people for directions',
    'Ask 3 different people for directions to a nearby location. This extends conversation beyond a simple greeting and requires active listening.',
    20
),
(
    'i1234567-1234-4321-i123-123456789002',
    'intermediate',
    'Give 3 genuine compliments',
    'Offer 3 authentic, specific compliments to strangers. Focus on choices they made (outfit, book, etc.) rather than physical attributes.',
    25
),
(
    'i1234567-1234-4321-i123-123456789003',
    'intermediate',
    'Have a 2-minute conversation',
    'Start a conversation with someone and keep it going for at least 2 minutes. Ask follow-up questions and share something about yourself.',
    30
)
ON CONFLICT (id) DO NOTHING;

-- Insert advanced level challenges
INSERT INTO "public"."approach_challenges" (
    "id", 
    "difficulty",
    "title",
    "description",
    "points"
) VALUES
(
    'a1234567-1234-4321-a123-123456789001',
    'advanced',
    'Start conversation with someone attractive',
    'Approach someone you find attractive and start a genuine conversation. Focus on connection, not conquest. Be authentic and respectful.',
    50
),
(
    'a1234567-1234-4321-a123-123456789002',
    'advanced', 
    'Get a phone number',
    'Have a great conversation and, if there''s mutual interest, ask for their phone number. Practice graceful acceptance of either yes or no.',
    75
),
(
    'a1234567-1234-4321-a123-123456789003',
    'advanced',
    'Plan an instant coffee meetup',
    'If conversation is going well, suggest grabbing coffee right then. This is about reading social cues and taking initiative while being respectful.',
    100
)
ON CONFLICT (id) DO NOTHING;

-- Insert bonus challenge for special occasions
INSERT INTO "public"."approach_challenges" (
    "id",
    "difficulty",
    "title",
    "description", 
    "points"
) VALUES
(
    'x1234567-1234-4321-x123-123456789001',
    'advanced',
    'Make someone laugh genuinely',
    'Use humor (not at anyone''s expense) to create a moment of genuine laughter in conversation. This builds authentic connection.',
    40
),
(
    'x1234567-1234-4321-x123-123456789002',
    'intermediate',
    'Give a book recommendation',
    'Recommend a book to someone based on something they mention in conversation. This shows you''re listening and creates potential follow-up.',
    25
),
(
    'x1234567-1234-4321-x123-123456789003',
    'beginner',
    'Hold a door and chat briefly',
    'Hold a door open for someone and make brief small talk about the weather or the venue. Practice extending kindness.',
    12
)
ON CONFLICT (id) DO NOTHING;

COMMIT;

-- Verification query to check inserted data
-- SELECT difficulty, COUNT(*) as challenge_count, AVG(points) as avg_points 
-- FROM approach_challenges 
-- GROUP BY difficulty 
-- ORDER BY 
--   CASE difficulty 
--     WHEN 'beginner' THEN 1 
--     WHEN 'intermediate' THEN 2 
--     WHEN 'advanced' THEN 3 
--   END;