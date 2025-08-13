-- Clean up all test users from creator_profiles_rows.sql
-- This includes auto-generated temp users and manual test accounts

-- Delete from teams_creators junction table first
DELETE FROM teams_creators
WHERE creator_profile_id IN (
  SELECT id FROM creator_profiles 
  WHERE slack_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
  OR zoom_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
);

-- Delete from project_updates
DELETE FROM project_updates
WHERE user_id IN (
  SELECT id FROM creator_profiles 
  WHERE slack_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
  OR zoom_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
);

-- Delete from project_overview_progress
DELETE FROM project_overview_progress
WHERE user_id IN (
  SELECT id FROM creator_profiles 
  WHERE slack_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
  OR zoom_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
);

-- Delete from project_overview
DELETE FROM project_overview
WHERE user_id IN (
  SELECT id FROM creator_profiles 
  WHERE slack_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
  OR zoom_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
);

-- Delete from longterm_memory
DELETE FROM longterm_memory
WHERE user_id IN (
  SELECT id FROM creator_profiles 
  WHERE slack_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
  OR zoom_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
);

-- Delete from memory
DELETE FROM memory
WHERE user_id IN (
  SELECT id FROM creator_profiles 
  WHERE slack_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
  OR zoom_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
);

-- Delete from interaction_metrics
DELETE FROM interaction_metrics
WHERE user_id IN (
  SELECT id FROM creator_profiles 
  WHERE slack_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
  OR zoom_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
);

-- Delete from creator_creativity_profiles
DELETE FROM creator_creativity_profiles
WHERE user_id IN (
  SELECT id FROM creator_profiles 
  WHERE slack_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
  OR zoom_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
);

-- Delete from beta_feedback
DELETE FROM beta_feedback
WHERE user_id IN (
  SELECT id FROM creator_profiles 
  WHERE slack_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
  OR zoom_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
);

-- Delete from agent_sessions
DELETE FROM agent_sessions
WHERE user_id IN (
  SELECT id FROM creator_profiles 
  WHERE slack_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
  OR zoom_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
);

-- Delete from applications
DELETE FROM applications
WHERE creator_profile_id IN (
  SELECT id FROM creator_profiles 
  WHERE slack_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
  OR zoom_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
);

-- Delete from user_feedback
DELETE FROM user_feedback
WHERE user_id IN (
  SELECT id FROM creator_profiles 
  WHERE slack_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
  OR zoom_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
);

-- Delete from conversations
DELETE FROM conversations
WHERE user_id IN (
  SELECT id FROM creator_profiles 
  WHERE slack_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
  OR zoom_email IN (
    -- Auto-generated temp users
    'user_11435053@temp.com',
    'user_120ef9a0@temp.com', 
    'user_18013f30@temp.com',
    'user_2146721a@temp.com',
    'user_6c432d35@temp.com',
    'user_f6056ddd@temp.com',
    -- Manual test accounts
    'isorabins@gmail.com',
    'projecttest626@gmail.com',
    'projecttest627@gmail.com',
    'projecttest3626@gmail.com',
    'authtest626@gmail.com',
    'test627@gmail.com',
    'test626@gmail.com',
    'iso@fridaysatfour.co',
    'projecttest@gmail.com',
    'projecttest2626@gmail.com',
    'authtest2626@gmail.com',
    -- Bug test user (auto-generated)
    'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
  )
);

-- Finally, delete the creator profiles themselves
DELETE FROM creator_profiles
WHERE slack_email IN (
  -- Auto-generated temp users
  'user_11435053@temp.com',
  'user_120ef9a0@temp.com', 
  'user_18013f30@temp.com',
  'user_2146721a@temp.com',
  'user_6c432d35@temp.com',
  'user_f6056ddd@temp.com',
  -- Manual test accounts
  'isorabins@gmail.com',
  'projecttest626@gmail.com',
  'projecttest627@gmail.com',
  'projecttest3626@gmail.com',
  'authtest626@gmail.com',
  'test627@gmail.com',
  'test626@gmail.com',
  'iso@fridaysatfour.co',
  'projecttest@gmail.com',
  'projecttest2626@gmail.com',
  'authtest2626@gmail.com',
  -- Bug test user (auto-generated)
  'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
)
OR zoom_email IN (
  -- Auto-generated temp users
  'user_11435053@temp.com',
  'user_120ef9a0@temp.com', 
  'user_18013f30@temp.com',
  'user_2146721a@temp.com',
  'user_6c432d35@temp.com',
  'user_f6056ddd@temp.com',
  -- Manual test accounts
  'isorabins@gmail.com',
  'projecttest626@gmail.com',
  'projecttest627@gmail.com',
  'projecttest3626@gmail.com',
  'authtest626@gmail.com',
  'test627@gmail.com',
  'test626@gmail.com',
  'iso@fridaysatfour.co',
  'projecttest@gmail.com',
  'projecttest2626@gmail.com',
  'authtest2626@gmail.com',
  -- Bug test user (auto-generated)
  'e686b39f-2069-46dd-a12e-81cc2c073e1b@bug-test.local'
);

-- Report the number of remaining profiles
SELECT COUNT(*) as remaining_profiles FROM creator_profiles; 

-- Show a sample of remaining profiles to verify cleanup
SELECT slack_email, zoom_email, first_name, last_name, created_at 
FROM creator_profiles 
ORDER BY created_at DESC 
LIMIT 10; 