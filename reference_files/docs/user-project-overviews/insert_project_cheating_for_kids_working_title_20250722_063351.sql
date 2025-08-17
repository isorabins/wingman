-- Project Overview Insert for dorian@artiface.ai
-- Generated on 2025-07-22 06:33:51

-- Verify user exists first
SELECT id, slack_email FROM creator_profiles WHERE id = 'c8e6db23-42fc-40e4-a0c6-5ec1732dd9ca';

-- Insert project overview
INSERT INTO "public"."project_overview" (
    "id",
    "user_id",
    "project_name", 
    "project_type",
    "description",
    "current_phase",
    "goals",
    "challenges",
    "success_metrics",
    "creation_date",
    "last_updated",
    "timeline",
    "weekly_commitment",
    "resources_needed",
    "working_style"
) VALUES (
    '06728c0c-d744-47de-b22e-02414966b3d5',
    'c8e6db23-42fc-40e4-a0c6-5ec1732dd9ca',
    'Cheating for Kids (working title)',
    'Non-fiction book',
    'A guide for children aged 8-14 that explores the complex reality of cheating in the adult world, addressing the contradiction between "cheating is wrong" messaging and observed adult behavior. The book aims to help children develop critical thinking about different forms of cheating, using modern examples like AI to illustrate the difference between clever adaptation and harmful cheating.',
    'planning',
    ARRAY['"Help children distinguish between clever and poor cheating as a life skill"'::jsonb, '"Change readers'' perspective on how they see the world"'::jsonb, '"Create meaningful impact through reader feedback"'::jsonb],
    ARRAY['"Life commitments impacting writing time"'::jsonb, '"Organizing material into structured format"'::jsonb, '"Ensuring content remains relatable to target age group"'::jsonb, '"Need for early reader testing and feedback"'::jsonb],
    '{"timeline": "- Overall: One year to completion - Weekly Commitment: 3-5 hours - Major milestones to be developed", "key_metrics": ["Reader feedback indicating shifted perspectives", "Successful communication of complex ideas in kid", "friendly format", "Positive engagement from target age group during testing"], "working_style": "- Regular gentle nudges and encouragement - Specific deadlines and clear goals - Direct feedback and accountability", "resources_needed": ["Mac for writing", "Online research materials", "Early reader testing group", "Research verification resources"], "weekly_commitment": "3-5 hours, preferably early morning or mid-evening", "success_definition": "- Reader feedback indicating shifted perspectives - Successful communication of complex ideas in kid-friendly format - Positive engagement from target age group during testing"}'::jsonb,
    NOW(),
    NOW(),
    '{}'::jsonb,
    '3-5 hours, preferably early morning or mid-evening',
    '{}'::jsonb,
    '- Regular gentle nudges and encouragement - Specific deadlines and clear goals - Direct feedback and accountability'
);

-- Verify insertion
SELECT 
    project_name,
    project_type,
    current_phase,
    array_length(goals, 1) as goals_count,
    array_length(challenges, 1) as challenges_count,
    weekly_commitment,
    creation_date
FROM project_overview 
WHERE user_id = 'c8e6db23-42fc-40e4-a0c6-5ec1732dd9ca' 
ORDER BY creation_date DESC 
LIMIT 1;
