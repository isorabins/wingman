-- Migration: Add skip tracking and intro flow support
-- Date: 2024-12-17
-- Purpose: Enable functional flow optimization with skip functionality and welcome flow

-- Add skip tracking to progress tables (CORRECTED approach)
ALTER TABLE creativity_test_progress 
ADD COLUMN skipped_until TIMESTAMP NULL,
ADD COLUMN has_seen_intro BOOLEAN DEFAULT FALSE,
ADD COLUMN intro_stage INTEGER DEFAULT 1,
ADD COLUMN intro_data JSONB DEFAULT '{}';

ALTER TABLE project_overview_progress 
ADD COLUMN skipped_until TIMESTAMP NULL;

-- Add indexes for performance
CREATE INDEX idx_creativity_test_progress_skipped_until ON creativity_test_progress(skipped_until);
CREATE INDEX idx_creativity_test_progress_intro_stage ON creativity_test_progress(intro_stage);
CREATE INDEX idx_project_overview_progress_skipped_until ON project_overview_progress(skipped_until);

-- Add helpful comments
COMMENT ON COLUMN creativity_test_progress.skipped_until IS 'Timestamp until which creativity test is skipped (24h periods)';
COMMENT ON COLUMN creativity_test_progress.has_seen_intro IS 'Whether user has completed the welcome/intro flow';
COMMENT ON COLUMN creativity_test_progress.intro_stage IS 'Current stage in intro flow (1-6, 6=complete)';
COMMENT ON COLUMN creativity_test_progress.intro_data IS 'Collected data during intro flow (name, project_info, etc.)';
COMMENT ON COLUMN project_overview_progress.skipped_until IS 'Timestamp until which project overview is skipped (24h periods)'; 