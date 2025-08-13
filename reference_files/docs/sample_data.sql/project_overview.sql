-- Sample conversation data for project tracking and updates
-- User: 09f94574-1817-454f-b123-deccdecc8dac
-- Project: Creative Writing Novel

INSERT INTO conversations (user_id, message_text, role, context, metadata, created_at) VALUES

-- Day 1: Project kickoff and initial planning
('09f94574-1817-454f-b123-deccdecc8dac', 
'Hey Hai! I''m ready to start working on my novel. I''ve been thinking about it all weekend and I''m feeling really energized - probably an 8/10 energy level. I want to tackle the character development first since that''s been on my mind.', 
'user', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"energy_level": 8, "mood": "excited", "focus_area": "character_development"}', 
'2024-01-15 09:00:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'That''s fantastic energy to start with! Character development is such a solid foundation. What specific character work are you planning to tackle this week? Are you thinking character profiles, backstories, or maybe exploring their voices through some practice scenes?', 
'assistant', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"response_type": "clarifying_question", "focus": "task_specificity"}', 
'2024-01-15 09:02:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'I want to create detailed profiles for my three main characters this week. I''m thinking 2-3 pages each covering their backgrounds, motivations, and key relationships. My goal is to finish all three by Friday so I can start the outline next week.', 
'user', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"tasks": ["character_profile_1", "character_profile_2", "character_profile_3"], "deadline": "2024-01-19", "estimated_hours": 12}', 
'2024-01-15 09:05:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'Perfect! That''s a concrete, achievable goal. Three detailed character profiles by Friday gives you about 4 hours per character if you''re working your planned 12 hours this week. How are you feeling about that timeline? Does it feel realistic with your other commitments?', 
'assistant', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"timeline_check": true, "workload_assessment": "realistic"}', 
'2024-01-15 09:07:00+00'),

-- Day 3: Mid-week check-in
('09f94574-1817-454f-b123-deccdecc8dac', 
'Quick update - I finished the first character profile yesterday! Sarah''s backstory really came together. I''m about 60% done with Marcus''s profile. Energy is still good, maybe 7/10. Planning to finish Marcus tonight and start Elena''s profile tomorrow.', 
'user', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"energy_level": 7, "progress": {"sarah_profile": "complete", "marcus_profile": 0.6, "elena_profile": 0}, "momentum": "strong"}', 
'2024-01-17 18:30:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'Excellent progress! You''re ahead of schedule and maintaining great momentum. I love that Sarah''s backstory "came together" - that feeling of pieces clicking into place is so satisfying. How did working on her profile influence your vision for Marcus? Sometimes developing one character reveals new things about the others.', 
'assistant', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"progress_acknowledgment": true, "creative_insight_prompt": true}', 
'2024-01-17 18:32:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'Actually yes! Working on Sarah made me realize Marcus needs to be more of a foil to her optimism. I''m adding some past disappointments to his background that will create interesting tension between them. This is exactly why I wanted to do the characters first - they''re informing each other.', 
'user', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"creative_breakthrough": true, "character_relationships": "developing", "methodology_validation": true}', 
'2024-01-17 18:35:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'That''s a beautiful example of the creative process working! Character dynamics emerging naturally as you develop them individually - you''re building the foundation for compelling conflict and growth. Keep trusting that instinct about letting characters inform each other.', 
'assistant', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"validation": true, "process_encouragement": true}', 
'2024-01-17 18:37:00+00'),

-- Day 5: Week completion and planning ahead
('09f94574-1817-454f-b123-deccdecc8dac', 
'All three character profiles are done! Finished Elena''s this morning. I''m feeling really accomplished - energy around 9/10. I want to start the chapter-by-chapter outline on Monday. Thinking I''ll aim for a 25-chapter structure, roughly 3,000 words per chapter.', 
'user', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"energy_level": 9, "milestone_completed": "character_profiles", "next_phase": "outline", "target_structure": {"chapters": 25, "words_per_chapter": 3000}}', 
'2024-01-19 10:15:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'Congratulations on completing all three profiles! That''s a significant milestone and your energy level shows it. 75,000 words across 25 chapters is a solid novel length. How long are you thinking the outline phase should take? And what level of detail are you planning for each chapter summary?', 
'assistant', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"milestone_celebration": true, "planning_assistance": true, "scope_clarification": true}', 
'2024-01-19 10:18:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'I''m thinking 2 weeks for the outline. I want each chapter summary to be about half a page - enough detail to know the key events, character development, and how it connects to the overall arc. Maybe 200-300 words per chapter outline.', 
'user', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"timeline": "2_weeks", "detail_level": "medium", "words_per_outline": 250, "total_outline_words": 6250}', 
'2024-01-19 10:22:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'That sounds like a thorough approach that will really set you up for success in the drafting phase. 6,000+ words of detailed outline work will save you so much time and decision fatigue when you''re writing. Are you planning to tackle the outline chronologically, or do you have key scenes you want to map out first?', 
'assistant', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"strategic_planning": true, "approach_clarification": true}', 
'2024-01-19 10:25:00+00'),

-- Day 8: Outline phase begins
('09f94574-1817-454f-b123-deccdecc8dac', 
'Started the outline work today. I''m going chronologically but I sketched out three key scenes first - the opening, the midpoint crisis, and the climax. Having those anchor points is helping me see the shape of the story. Energy is good, around 7/10. Got chapters 1-3 outlined today.', 
'user', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"energy_level": 7, "progress": {"chapters_outlined": 3, "key_scenes_mapped": 3}, "methodology": "chronological_with_anchors"}', 
'2024-01-22 16:45:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'Smart strategy with the anchor points! That''s giving you a roadmap to write toward. Three chapters outlined in one day is excellent progress. How are you finding the pacing as you work through the early chapters? Are you discovering new plot threads or staying close to your original vision?', 
'assistant', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"strategy_validation": true, "creative_discovery_check": true}', 
'2024-01-22 16:48:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'I''m staying pretty close to my original vision but adding more texture. Like, I knew Sarah would have a conflict with her sister, but as I''m outlining, I''m realizing it needs to happen earlier and be more central to her character arc. The outline is helping me see structural issues before I write myself into corners.', 
'user', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"story_evolution": true, "structural_insights": true, "plot_refinement": "sister_conflict_timing"}', 
'2024-01-