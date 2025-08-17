-- Add feature flags and deployment infrastructure tables
-- Migration: 007_add_feature_flags_and_deployment_tables.sql

-- Feature flags table for runtime configuration
CREATE TABLE IF NOT EXISTS feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT false,
    description TEXT NOT NULL,
    environment VARCHAR(20) NOT NULL DEFAULT 'all',
    rollout_percentage INTEGER NOT NULL DEFAULT 100 CHECK (rollout_percentage >= 0 AND rollout_percentage <= 100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- Indexes for feature flags
CREATE INDEX idx_feature_flags_name ON feature_flags(name);
CREATE INDEX idx_feature_flags_enabled ON feature_flags(enabled);
CREATE INDEX idx_feature_flags_environment ON feature_flags(environment);

-- RLS policies for feature flags
ALTER TABLE feature_flags ENABLE ROW LEVEL SECURITY;

-- Allow read access to feature flags for authenticated users
CREATE POLICY "Users can read feature flags" ON feature_flags
    FOR SELECT USING (true);

-- Allow service role to manage feature flags
CREATE POLICY "Service role can manage feature flags" ON feature_flags
    FOR ALL USING (auth.role() = 'service_role');

-- Deployment logs table for tracking deployments
CREATE TABLE IF NOT EXISTS deployment_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deployment_id VARCHAR(100) NOT NULL,
    deployment_type VARCHAR(50) NOT NULL,
    environment VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'started', 'in_progress', 'completed', 'failed', 'rolled_back'
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    steps_total INTEGER,
    steps_completed INTEGER,
    steps_failed INTEGER,
    failure_reason TEXT,
    rollback_executed BOOLEAN DEFAULT false,
    deployment_log JSONB,
    created_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for deployment logs
CREATE INDEX idx_deployment_logs_deployment_id ON deployment_logs(deployment_id);
CREATE INDEX idx_deployment_logs_status ON deployment_logs(status);
CREATE INDEX idx_deployment_logs_environment ON deployment_logs(environment);
CREATE INDEX idx_deployment_logs_start_time ON deployment_logs(start_time);

-- RLS policies for deployment logs
ALTER TABLE deployment_logs ENABLE ROW LEVEL SECURITY;

-- Allow service role to manage deployment logs
CREATE POLICY "Service role can manage deployment logs" ON deployment_logs
    FOR ALL USING (auth.role() = 'service_role');

-- Allow authenticated users to read deployment logs
CREATE POLICY "Users can read deployment logs" ON deployment_logs
    FOR SELECT USING (auth.role() = 'authenticated');

-- System health metrics table for monitoring
CREATE TABLE IF NOT EXISTS system_health_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    environment VARCHAR(20) NOT NULL,
    overall_healthy BOOLEAN NOT NULL,
    database_healthy BOOLEAN NOT NULL,
    redis_healthy BOOLEAN NOT NULL,
    email_healthy BOOLEAN NOT NULL,
    monitoring_healthy BOOLEAN NOT NULL,
    response_time_ms INTEGER,
    active_alerts INTEGER,
    performance_score INTEGER CHECK (performance_score >= 0 AND performance_score <= 100),
    health_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for system health metrics
CREATE INDEX idx_system_health_metrics_timestamp ON system_health_metrics(metric_timestamp);
CREATE INDEX idx_system_health_metrics_environment ON system_health_metrics(environment);
CREATE INDEX idx_system_health_metrics_overall_healthy ON system_health_metrics(overall_healthy);

-- RLS policies for system health metrics
ALTER TABLE system_health_metrics ENABLE ROW LEVEL SECURITY;

-- Allow service role to manage health metrics
CREATE POLICY "Service role can manage health metrics" ON system_health_metrics
    FOR ALL USING (auth.role() = 'service_role');

-- Allow authenticated users to read health metrics
CREATE POLICY "Users can read health metrics" ON system_health_metrics
    FOR SELECT USING (auth.role() = 'authenticated');

-- Insert default feature flags
INSERT INTO feature_flags (name, enabled, description, environment, rollout_percentage, created_by)
VALUES 
    ('enhanced_monitoring', true, 'Enable enhanced monitoring and observability features', 'all', 100, 'system'),
    ('external_alerts', true, 'Enable external alert notifications (Slack, email)', 'all', 100, 'system'),
    ('backup_verification', true, 'Enable automated backup verification system', 'all', 100, 'system'),
    ('performance_optimization', true, 'Enable performance optimization features', 'all', 100, 'system'),
    ('canary_deployments', false, 'Enable canary deployment features for gradual rollouts', 'production', 0, 'system'),
    ('blue_green_deployment', false, 'Enable blue-green deployment capabilities', 'production', 0, 'system'),
    ('advanced_analytics', false, 'Enable advanced analytics and user behavior tracking', 'all', 0, 'system'),
    ('a_b_testing', false, 'Enable A/B testing framework for feature experimentation', 'all', 0, 'system'),
    ('rate_limiting_enhanced', true, 'Enable enhanced rate limiting with user-specific quotas', 'all', 100, 'system'),
    ('real_time_notifications', false, 'Enable real-time push notifications for matches and messages', 'all', 0, 'system'),
    ('ai_coaching_v2', false, 'Enable next-generation AI coaching features', 'all', 0, 'system'),
    ('voice_messages', false, 'Enable voice message functionality in chat', 'all', 0, 'system'),
    ('video_sessions', false, 'Enable video session functionality for wingman meetings', 'all', 0, 'system'),
    ('premium_features', false, 'Enable premium subscription features', 'all', 0, 'system')
ON CONFLICT (name) DO NOTHING;

-- Function to update updated_at timestamp on feature flags
CREATE OR REPLACE FUNCTION update_feature_flags_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_feature_flags_updated_at
    BEFORE UPDATE ON feature_flags
    FOR EACH ROW
    EXECUTE FUNCTION update_feature_flags_updated_at();

-- Function to clean up old health metrics (keep last 7 days)
CREATE OR REPLACE FUNCTION cleanup_old_health_metrics()
RETURNS void AS $$
BEGIN
    DELETE FROM system_health_metrics 
    WHERE created_at < NOW() - INTERVAL '7 days';
END;
$$ language 'plpgsql';

-- Function to clean up old deployment logs (keep last 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_deployment_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM deployment_logs 
    WHERE created_at < NOW() - INTERVAL '30 days';
END;
$$ language 'plpgsql';

-- Comments for documentation
COMMENT ON TABLE feature_flags IS 'Runtime feature flags for controlling application behavior without deployments';
COMMENT ON TABLE deployment_logs IS 'Log of deployment activities and their outcomes';
COMMENT ON TABLE system_health_metrics IS 'System health monitoring data for observability';

COMMENT ON COLUMN feature_flags.rollout_percentage IS 'Percentage of users who should see this feature (0-100)';
COMMENT ON COLUMN feature_flags.environment IS 'Environment where this flag applies (all, production, development)';
COMMENT ON COLUMN deployment_logs.deployment_log IS 'Detailed JSON log of deployment steps and results';
COMMENT ON COLUMN system_health_metrics.health_details IS 'Detailed JSON health check results';
