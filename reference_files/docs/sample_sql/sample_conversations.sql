-- Sample conversation data for project tracking and updates
-- User: 09f94574-1817-454f-b123-deccdecc8dac
-- Project: Creative Writing Novel - July 2nd, 2025

INSERT INTO conversations (user_id, message_text, role, context, metadata, created_at) VALUES

-- Morning: Project kickoff and task planning
('09f94574-1817-454f-b123-deccdecc8dac', 
'Good morning Hai! I''m ready to dive into my novel today. I''m feeling really energized - probably an 8/10 energy level. I want to tackle revising chapters 3-5 today since I got some feedback from my beta reader yesterday that those need work.', 
'user', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"energy_level": 8, "mood": "focused", "focus_area": "revision", "chapters_target": [3, 4, 5]}', 
'2025-07-02 08:30:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'Great energy to start the day with! Beta reader feedback is so valuable. What specific issues did they identify in chapters 3-5? Are we talking about pacing, character development, or plot clarity? Understanding the feedback will help us prioritize your revision approach.', 
'assistant', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"response_type": "clarifying_question", "focus": "feedback_analysis"}', 
'2025-07-02 08:32:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'The main issue is pacing - chapters 3 and 4 drag a bit, and chapter 5 rushes through what should be a major emotional moment. They said Sarah''s reaction to finding her sister''s letters feels rushed. I need to cut about 800 words from chapter 3, tighten chapter 4, and expand chapter 5 by maybe 1200 words.', 
'user', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"revision_tasks": {"chapter_3": "cut_800_words", "chapter_4": "tighten_pacing", "chapter_5": "expand_1200_words"}, "focus_scene": "sister_letters_discovery"}', 
'2025-07-02 08:35:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'That''s really specific, actionable feedback! The emotional moment with the letters definitely deserves more space. How are you planning to approach this? Are you thinking of tackling one chapter at a time, or do you want to map out the changes across all three first?', 
'assistant', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"strategy_planning": true, "approach_options": ["sequential", "holistic_mapping"]}', 
'2025-07-02 08:37:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'I think I''ll start with chapter 3 since cutting is usually easier than expanding. Get that tightened up, then move to chapter 4, and save chapter 5 for last when my energy is still good for the creative expansion work. Planning to spend about 2 hours on each chapter.', 
'user', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"strategy": "sequential_easy_to_hard", "time_allocation": {"per_chapter": 2, "total_planned": 6}, "reasoning": "save_creative_work_for_peak_energy"}', 
'2025-07-02 08:40:00+00'),

-- Mid-morning: First chapter revision update
('09f94574-1817-454f-b123-deccdecc8dac', 
'Just finished chapter 3 revision! Cut 850 words and it flows much better now. I found a whole paragraph that was just repeating information from chapter 2. Energy still strong at 7/10. Moving on to chapter 4 now.', 
'user', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"energy_level": 7, "progress": {"chapter_3": "complete", "words_cut": 850}, "discovery": "redundant_paragraph_removed", "next_task": "chapter_4"}', 
'2025-07-02 10:45:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'Excellent work! Finding redundant content is so satisfying - it''s like discovering you can make something better just by removing what doesn''t belong. How did it feel to cut more than your target? Sometimes being a bit more aggressive with cuts can really sharpen the prose.', 
'assistant', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"progress_validation": true, "editing_insight": true, "process_reflection": true}', 
'2025-07-02 10:47:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'It felt great! I was worried about cutting too much, but every sentence I removed made the remaining ones stronger. I''m getting better at being ruthless with my own work. Chapter 4 is looking like it needs similar treatment - there''s a conversation that goes in circles.', 
'user', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"confidence_building": true, "editing_skill_development": true, "chapter_4_issue": "circular_conversation"}', 
'2025-07-02 10:50:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'That''s a huge breakthrough in your editing mindset! Being able to cut your own work effectively is such a valuable skill. Circular conversations are tricky - sometimes they''re realistic but not serving the story. Trust your instincts on what needs to go.', 
'assistant', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"skill_recognition": true, "confidence_boost": true, "editing_guidance": true}', 
'2025-07-02 10:52:00+00'),

-- Lunch break and afternoon session
('09f94574-1817-454f-b123-deccdecc8dac', 
'Back from lunch and finished chapter 4! The circular conversation is gone and I added a small action beat that moves the plot forward. Energy dipped to about 5/10 after lunch but I''m pushing through. Ready to tackle the big challenge - expanding chapter 5 for the emotional scene.', 
'user', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"energy_level": 5, "progress": {"chapter_4": "complete", "improvement": "added_action_beat"}, "challenge_ahead": "chapter_5_expansion", "determination": "pushing_through"}', 
'2025-07-02 13:30:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'You''re doing amazing work today! Two chapters revised and improved. I know your energy dipped, but you''re tackling the most challenging part - that shows real commitment. For the emotional expansion in chapter 5, are you thinking of adding internal monologue, more sensory details, or extending the dialogue?', 
'assistant', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"encouragement": true, "commitment_recognition": true, "expansion_strategy_options": ["internal_monologue", "sensory_details", "extended_dialogue"]}', 
'2025-07-02 13:32:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'I think a combination - more internal monologue to show Sarah''s emotional process, and definitely more sensory details. When she''s reading those letters, I want the reader to feel the paper texture, smell the old perfume, see how her hands shake. The dialogue is actually fine, it''s the emotional landscape that needs expanding.', 
'user', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"expansion_strategy": "internal_monologue_plus_sensory", "specific_details": ["paper_texture", "old_perfume", "shaking_hands"], "dialogue_assessment": "adequate"}', 
'2025-07-02 13:35:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'Perfect approach! You''re thinking like a filmmaker - creating a full sensory experience for that pivotal moment. The physical details you mentioned will ground the emotion in something tangible. Take your time with this scene; it sounds like it''s a crucial turning point for Sarah.', 
'assistant', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"approach_validation": true, "filmmaker_analogy": true, "scene_importance_recognition": true}', 
'2025-07-02 13:37:00+00'),

-- Late afternoon: Major breakthrough
('09f94574-1817-454f-b123-deccdecc8dac', 
'Hai, something amazing just happened! While expanding the letter scene, I realized Sarah needs to find a specific letter that changes everything - one where her sister mentions feeling trapped in her marriage. This gives Sarah a new motivation for the rest of the book. I''m so excited I can barely sit still! Energy back up to 9/10.', 
'user', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"energy_level": 9, "major_breakthrough": true, "plot_discovery": "sister_trapped_marriage_letter", "story_impact": "new_motivation_for_sarah", "excitement_level": "high"}', 
'2025-07-02 15:20:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'This is incredible! This is exactly the kind of discovery that makes revision so powerful - you''re not just fixing problems, you''re uncovering deeper layers of your story. A letter about feeling trapped that gives Sarah new purpose? That''s going to ripple through the entire narrative. How does this change your vision for the later chapters?', 
'assistant', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"breakthrough_celebration": true, "revision_power_recognition": true, "story_impact_analysis": true, "forward_planning_prompt": true}', 
'2025-07-02 15:22:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'It changes everything! Sarah''s not just grieving anymore - she''s on a mission to understand her sister''s life and maybe help other women who feel trapped. I need to go back and plant some seeds in earlier chapters, and I think the ending needs to be more hopeful now. This is why I love writing!', 
'user', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"story_transformation": "grief_to_mission", "revision_tasks": "plant_earlier_seeds", "tone_shift": "more_hopeful_ending", "writing_passion": "renewed"}', 
'2025-07-02 15:25:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'Yes! This is the magic of the creative process - when a story starts revealing itself to you in new ways. Your book is evolving from a grief story into something about purpose and helping others. That''s a powerful transformation. Are you going to make notes about the earlier seeds now, or finish this chapter first?', 
'assistant', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"creative_magic_recognition": true, "story_evolution_summary": true, "practical_next_steps": true}', 
'2025-07-02 15:27:00+00'),

-- Evening: Wrapping up and planning ahead
('09f94574-1817-454f-b123-deccdecc8dac', 
'I finished chapter 5 and made notes about the seeds to plant. Added 1,400 words and the scene is so much more powerful now. I''m exhausted but in the best way - energy down to about 4/10 but satisfaction is through the roof. Tomorrow I want to start planting those seeds in chapters 1-2.', 
'user', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"energy_level": 4, "satisfaction": "maximum", "chapter_5": "complete", "words_added": 1400, "tomorrow_plan": "plant_seeds_chapters_1_2", "fatigue_type": "good_exhaustion"}', 
'2025-07-02 18:45:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'What an incredible day of work! You accomplished everything you set out to do and discovered something that''s going to make your whole book stronger. That''s the kind of productive exhaustion that feels amazing. How long do you think the seed-planting revision will take?', 
'assistant', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"day_summary_celebration": true, "accomplishment_recognition": true, "planning_assistance": true}', 
'2025-07-02 18:47:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'Probably 2-3 days to do it right. I need to be subtle about it - just small hints and moments that will make the letter revelation feel inevitable rather than surprising. Then I think I''ll be ready to tackle the ending chapters with this new direction. This project feels so much more alive now!', 
'user', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"timeline_estimate": "2_3_days", "approach": "subtle_foreshadowing", "goal": "inevitable_not_surprising", "next_phase": "ending_chapters", "project_vitality": "renewed"}', 
'2025-07-02 18:50:00+00'),

('09f94574-1817-454f-b123-deccdecc8dac', 
'That''s exactly the right approach - foreshadowing that feels natural and inevitable. Your instincts about the craft are really developing. Celebrate this breakthrough! You''ve not only improved three chapters today but discovered a deeper truth about your story. That''s extraordinary work.', 
'assistant', 
'{"thread_id": "writing-project-main", "session_type": "project_update"}', 
'{"craft_development_recognition": true, "celebration_encouragement": true, "day_achievement_summary": true, "extraordinary_validation": true}', 
'2025-07-02 18:52:00+00');