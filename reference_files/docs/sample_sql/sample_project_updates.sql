-- Sample project updates for the past week (June 25 - July 2, 2025)
-- User: 09f94574-1817-454f-b123-deccdecc8dac
-- Assumes project_id exists from project_overview table

-- First, we need to get the project_id (this would be done in a real scenario)
-- For this example, let's assume the project_id is generated from the project_overview insert

WITH project_info AS (
  SELECT id as project_id FROM project_overview 
  WHERE user_id = '09f94574-1817-454f-b123-deccdecc8dac' 
  LIMIT 1
)

INSERT INTO project_updates (
    project_id, 
    user_id, 
    update_date, 
    progress_summary, 
    milestones_hit, 
    blockers, 
    next_steps, 
    mood_rating, 
    created_at
) 
SELECT 
    project_info.project_id,
    '09f94574-1817-454f-b123-deccdecc8dac',
    update_date,
    progress_summary,
    milestones_hit,
    blockers,
    next_steps,
    mood_rating,
    created_at
FROM project_info,
(VALUES
    -- June 25, 2025 - Week start, planning phase
    ('2025-06-25'::date, 
     'Started the week by outlining the character development arc for Maya, the protagonist. Spent 3 hours researching contemporary young adult themes and reading similar novels for inspiration. Created a detailed character profile and backstory.',
     ARRAY['Completed protagonist character profile', 'Researched 5 comparable YA novels', 'Established character voice and tone'],
     ARRAY['Struggling with the opening scene - feels too generic', 'Need to find beta readers for early feedback'],
     ARRAY['Write three different opening scene drafts', 'Reach out to local writing group for beta readers', 'Complete supporting character profiles'],
     4,
     '2025-06-25 18:30:00+00'::timestamptz),

    -- June 26, 2025 - Character development day
    ('2025-06-26'::date,
     'Deep dive into supporting characters today. Developed Maya''s best friend Zoe and her complicated relationship with her parents. Energy level was high (7/10) - the characters are really starting to feel real. Wrote 1,200 words of character backstory.',
     ARRAY['Created detailed profiles for 3 supporting characters', 'Wrote 1,200 words of character backstory', 'Established family dynamics and conflicts'],
     ARRAY['Characters feel too similar in voice', 'Need more diversity in character backgrounds'],
     ARRAY['Revise character voices to be more distinct', 'Research diverse cultural backgrounds', 'Start plotting chapter outline'],
     4,
     '2025-06-26 20:15:00+00'::timestamptz),

    -- June 27, 2025 - Plot development
    ('2025-06-27'::date,
     'Plot breakthrough! Finally figured out the central conflict - it''s not just about Maya''s identity crisis, but how she navigates family expectations vs. personal dreams. Outlined 15 chapters with major plot points. Feeling really energized about the direction.',
     ARRAY['Completed 15-chapter outline', 'Identified central theme and conflict', 'Mapped character arcs to plot progression'],
     ARRAY['Chapter 8-10 feel rushed in pacing', 'Need stronger subplot to support main narrative'],
     ARRAY['Develop romantic subplot details', 'Research pacing techniques for middle chapters', 'Start writing Chapter 1 draft'],
     5,
     '2025-06-27 19:45:00+00'::timestamptz),

    -- June 28, 2025 - First chapter draft
    ('2025-06-28'::date,
     'Wrote the first draft of Chapter 1! 2,800 words that establish Maya''s world and the inciting incident. It''s rough but captures the voice I want. Energy dipped a bit (6/10) due to self-doubt, but pushed through. The opening scene finally feels authentic.',
     ARRAY['Completed first draft of Chapter 1 (2,800 words)', 'Established protagonist voice and tone', 'Created compelling opening scene'],
     ARRAY['Worried about pacing in the opening', 'Some dialogue feels stilted', 'Second-guessing character motivations'],
     ARRAY['Let Chapter 1 sit for 2 days before revising', 'Start Chapter 2 outline', 'Join online YA writing community for feedback'],
     3,
     '2025-06-28 21:20:00+00'::timestamptz),

    -- June 29, 2025 - Research and planning
    ('2025-06-29'::date,
     'Research day focused on the contemporary issues Maya faces. Interviewed 3 teenagers about social media pressure and college expectations. Their insights were invaluable - completely shifted my perspective on how teens actually talk and think. Energy level good (7/10).',
     ARRAY['Conducted 3 interviews with target demographic', 'Updated character dialogue to be more authentic', 'Researched contemporary teen social issues'],
     ARRAY['Balancing authenticity with readability', 'Some research contradicts my initial assumptions'],
     ARRAY['Incorporate interview insights into character development', 'Revise Chapter 1 dialogue', 'Plan Chapter 2 writing session'],
     4,
     '2025-06-29 17:30:00+00'::timestamptz),

    -- June 30, 2025 - Weekend writing sprint
    ('2025-06-30'::date,
     'Saturday writing sprint! Dedicated 4 hours to writing and managed 3,100 words across Chapter 2 and revisions to Chapter 1. The story is gaining momentum. Maya''s voice is becoming clearer and more distinct. Feeling really good about progress.',
     ARRAY['Wrote 3,100 words total', 'Completed Chapter 2 first draft', 'Revised Chapter 1 dialogue and pacing', 'Established consistent daily writing routine'],
     ARRAY['Time management - need to balance writing with research', 'Physical fatigue from long writing sessions'],
     ARRAY['Set up ergonomic writing space', 'Plan shorter, more frequent writing sessions', 'Start Chapter 3 outline'],
     5,
     '2025-06-30 22:10:00+00'::timestamptz),

    -- July 1, 2025 - Revision and feedback
    ('2025-07-01'::date,
     'Connected with local writing group and shared Chapter 1 for feedback. Mixed reactions but overall positive. One member said Maya''s voice reminded them of their teenage daughter. Made notes on suggested improvements. Energy moderate (6/10) due to feedback anxiety.',
     ARRAY['Shared work with writing group for first time', 'Received constructive feedback on Chapter 1', 'Connected with potential ongoing critique partners'],
     ARRAY['Feedback anxiety affecting confidence', 'Conflicting opinions on character development approach'],
     ARRAY['Process feedback and create revision plan', 'Schedule regular critique sessions', 'Continue Chapter 3 development'],
     3,
     '2025-07-01 19:00:00+00'::timestamptz),

    -- July 2, 2025 - Today's progress
    ('2025-07-02'::date,
     'Great momentum today! Incorporated yesterday''s feedback and the opening chapter feels much stronger. Started Chapter 3 and the story is really flowing. Had a breakthrough with Maya''s internal conflict - it''s more nuanced than I initially planned. Energy high (8/10).',
     ARRAY['Revised Chapter 1 based on feedback', 'Started Chapter 3 (1,400 words)', 'Refined Maya''s character arc and internal conflict', 'Established sustainable writing routine'],
     ARRAY['Need to maintain consistency in supporting character development', 'Balancing multiple plot threads'],
     ARRAY['Continue Chapter 3 development', 'Plan character development sessions for supporting cast', 'Research publishing options for YA fiction'],
     4,
     '2025-07-02 16:30:00+00'::timestamptz)
) AS updates(update_date, progress_summary, milestones_hit, blockers, next_steps, mood_rating, created_at);