-- Migration: System Tables and Analytics for Red Legion Bot
-- Date: September 8, 2025
-- Purpose: Support system monitoring, analytics, user tracking, and administrative features

-- User activity tracking
CREATE TABLE IF NOT EXISTS user_activity (
    activity_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    user_id VARCHAR(20),
    username VARCHAR(100),
    activity_type VARCHAR(30) NOT NULL CHECK (activity_type IN (
        'command_used', 'event_joined', 'event_created', 'market_listing', 
        'loan_requested', 'loan_approved', 'application_submitted', 
        'message_sent', 'voice_joined', 'reaction_added'
    )),
    activity_details JSON,
    channel_id VARCHAR(20),
    channel_name VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System notifications and announcements
CREATE TABLE IF NOT EXISTS system_notifications (
    notification_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    notification_type VARCHAR(20) NOT NULL CHECK (notification_type IN ('announcement', 'alert', 'maintenance', 'update', 'reminder')),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    priority VARCHAR(10) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'critical')),
    target_roles JSON, -- Array of role IDs to notify
    target_channels JSON, -- Array of channel IDs to post in
    created_by_id VARCHAR(20),
    created_by_name VARCHAR(100),
    scheduled_date TIMESTAMP,
    sent_date TIMESTAMP,
    is_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bot configuration and feature toggles
CREATE TABLE IF NOT EXISTS bot_config (
    config_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    config_key VARCHAR(50) NOT NULL,
    config_value TEXT,
    config_type VARCHAR(20) DEFAULT 'string' CHECK (config_type IN ('string', 'integer', 'boolean', 'json')),
    description TEXT,
    is_editable BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, config_key)
);

-- User preferences and settings
CREATE TABLE IF NOT EXISTS user_preferences (
    preference_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    user_id VARCHAR(20),
    username VARCHAR(100),
    preference_key VARCHAR(50) NOT NULL,
    preference_value TEXT,
    preference_type VARCHAR(20) DEFAULT 'string' CHECK (preference_type IN ('string', 'integer', 'boolean', 'json')),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, user_id, preference_key)
);

-- Audit log for administrative actions
CREATE TABLE IF NOT EXISTS audit_log (
    log_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    user_id VARCHAR(20),
    username VARCHAR(100),
    action_type VARCHAR(30) NOT NULL CHECK (action_type IN (
        'user_banned', 'user_kicked', 'user_warned', 'role_assigned', 'role_removed',
        'channel_created', 'channel_deleted', 'permissions_changed', 'settings_updated',
        'event_deleted', 'market_item_removed', 'loan_cancelled', 'application_denied'
    )),
    target_id VARCHAR(20), -- ID of the target (user, channel, role, etc.)
    target_name VARCHAR(100),
    action_details JSON,
    reason TEXT,
    channel_id VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System statistics and metrics
CREATE TABLE IF NOT EXISTS system_metrics (
    metric_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(15,2),
    metric_date DATE DEFAULT CURRENT_DATE,
    additional_data JSON,
    UNIQUE(guild_id, metric_name, metric_date)
);

-- Error logging and debugging
CREATE TABLE IF NOT EXISTS error_logs (
    error_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20),
    error_type VARCHAR(50),
    error_message TEXT,
    error_details JSON,
    user_id VARCHAR(20),
    command_name VARCHAR(50),
    channel_id VARCHAR(20),
    stack_trace TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Feature usage analytics
CREATE TABLE IF NOT EXISTS feature_analytics (
    analytics_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    feature_name VARCHAR(50) NOT NULL,
    usage_count INTEGER DEFAULT 1,
    unique_users JSON, -- Array of user IDs who used this feature
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_date DATE DEFAULT CURRENT_DATE,
    UNIQUE(guild_id, feature_name, usage_date)
);

-- Scheduled tasks and reminders
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    task_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    task_type VARCHAR(30) NOT NULL CHECK (task_type IN (
        'event_reminder', 'loan_reminder', 'application_followup', 
        'backup_data', 'cleanup_old_data', 'send_notification'
    )),
    task_name VARCHAR(100) NOT NULL,
    task_data JSON,
    scheduled_time TIMESTAMP NOT NULL,
    repeat_interval VARCHAR(20), -- 'daily', 'weekly', 'monthly', etc.
    is_active BOOLEAN DEFAULT TRUE,
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    run_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for system tables
CREATE INDEX IF NOT EXISTS idx_user_activity_guild ON user_activity(guild_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_user ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_type ON user_activity(activity_type);
CREATE INDEX IF NOT EXISTS idx_user_activity_timestamp ON user_activity(timestamp);

CREATE INDEX IF NOT EXISTS idx_system_notifications_guild ON system_notifications(guild_id);
CREATE INDEX IF NOT EXISTS idx_system_notifications_type ON system_notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_system_notifications_sent ON system_notifications(is_sent);
CREATE INDEX IF NOT EXISTS idx_system_notifications_scheduled ON system_notifications(scheduled_date);

CREATE INDEX IF NOT EXISTS idx_bot_config_guild ON bot_config(guild_id);
CREATE INDEX IF NOT EXISTS idx_bot_config_key ON bot_config(config_key);

CREATE INDEX IF NOT EXISTS idx_user_preferences_guild_user ON user_preferences(guild_id, user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_key ON user_preferences(preference_key);

CREATE INDEX IF NOT EXISTS idx_audit_log_guild ON audit_log(guild_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);

CREATE INDEX IF NOT EXISTS idx_system_metrics_guild ON system_metrics(guild_id);
CREATE INDEX IF NOT EXISTS idx_system_metrics_name ON system_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_system_metrics_date ON system_metrics(metric_date);

CREATE INDEX IF NOT EXISTS idx_error_logs_guild ON error_logs(guild_id);
CREATE INDEX IF NOT EXISTS idx_error_logs_type ON error_logs(error_type);
CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp ON error_logs(timestamp);

CREATE INDEX IF NOT EXISTS idx_feature_analytics_guild ON feature_analytics(guild_id);
CREATE INDEX IF NOT EXISTS idx_feature_analytics_feature ON feature_analytics(feature_name);
CREATE INDEX IF NOT EXISTS idx_feature_analytics_date ON feature_analytics(usage_date);

CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_guild ON scheduled_tasks(guild_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_type ON scheduled_tasks(task_type);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_active ON scheduled_tasks(is_active);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_next_run ON scheduled_tasks(next_run);

-- Insert default bot configuration settings
INSERT INTO bot_config (guild_id, config_key, config_value, config_type, description, is_editable)
SELECT DISTINCT 
    guild_id,
    unnest(ARRAY[
        'default_event_category', 'default_market_category', 'auto_role_assignment',
        'max_loan_amount', 'loan_interest_rate', 'application_auto_archive_days',
        'event_reminder_hours', 'market_cleanup_days', 'activity_tracking_enabled',
        'error_logging_enabled', 'analytics_enabled', 'maintenance_mode'
    ]),
    unnest(ARRAY[
        'mining', 'ships', 'true',
        '1000000', '0.05', '30',
        '24', '90', 'true',
        'true', 'true', 'false'
    ]),
    unnest(ARRAY[
        'string', 'string', 'boolean',
        'integer', 'string', 'integer',
        'integer', 'integer', 'boolean',
        'boolean', 'boolean', 'boolean'
    ]),
    unnest(ARRAY[
        'Default category for new events', 'Default category for market listings', 'Automatically assign roles on approval',
        'Maximum loan amount in UEC', 'Default interest rate for loans', 'Days before auto-archiving applications',
        'Hours before event reminder', 'Days before cleaning up old market listings', 'Track user activity',
        'Log errors to database', 'Track feature usage analytics', 'Bot maintenance mode'
    ]),
    unnest(ARRAY[
        true, true, true,
        true, true, true,
        true, true, true,
        false, true, false
    ])
FROM guilds
ON CONFLICT (guild_id, config_key) DO NOTHING;

-- Create views for system analytics
CREATE OR REPLACE VIEW daily_activity_summary AS
SELECT 
    guild_id,
    DATE(timestamp) as activity_date,
    COUNT(*) as total_activities,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(*) FILTER (WHERE activity_type = 'command_used') as commands_used,
    COUNT(*) FILTER (WHERE activity_type = 'event_joined') as events_joined,
    COUNT(*) FILTER (WHERE activity_type = 'event_created') as events_created,
    COUNT(*) FILTER (WHERE activity_type = 'market_listing') as market_listings,
    COUNT(*) FILTER (WHERE activity_type = 'loan_requested') as loan_requests,
    COUNT(*) FILTER (WHERE activity_type = 'application_submitted') as applications_submitted
FROM user_activity
WHERE timestamp >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY guild_id, DATE(timestamp)
ORDER BY guild_id, activity_date DESC;

CREATE OR REPLACE VIEW feature_usage_summary AS
SELECT 
    f.guild_id,
    f.feature_name,
    SUM(f.usage_count) as total_uses,
    COUNT(DISTINCT f.usage_date) as days_used,
    MAX(f.last_used) as last_used,
    AVG(f.usage_count) as avg_daily_uses,
    ARRAY_LENGTH(
        ARRAY(
            SELECT DISTINCT unnest_users 
            FROM (
                SELECT unnest(f2.unique_users::text[]::varchar[]) as unnest_users 
                FROM feature_analytics f2 
                WHERE f2.guild_id = f.guild_id AND f2.feature_name = f.feature_name
            ) sub
        ), 1
    ) as unique_users_count
FROM feature_analytics f
WHERE f.usage_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY f.guild_id, f.feature_name
ORDER BY f.guild_id, total_uses DESC;

CREATE OR REPLACE VIEW system_health_summary AS
SELECT 
    COALESCE(e.guild_id, 'SYSTEM') as guild_id,
    COUNT(*) as total_errors,
    COUNT(DISTINCT e.error_type) as unique_error_types,
    COUNT(*) FILTER (WHERE e.timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours') as errors_last_24h,
    COUNT(*) FILTER (WHERE e.timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days') as errors_last_7d,
    MAX(e.timestamp) as last_error_time,
    MODE() WITHIN GROUP (ORDER BY e.error_type) as most_common_error
FROM error_logs e
WHERE e.timestamp >= CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY e.guild_id
ORDER BY total_errors DESC;

-- Functions for analytics and maintenance
CREATE OR REPLACE FUNCTION log_user_activity(
    p_guild_id VARCHAR(20),
    p_user_id VARCHAR(20),
    p_username VARCHAR(100),
    p_activity_type VARCHAR(30),
    p_activity_details JSON DEFAULT NULL,
    p_channel_id VARCHAR(20) DEFAULT NULL,
    p_channel_name VARCHAR(100) DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO user_activity (
        guild_id, user_id, username, activity_type, 
        activity_details, channel_id, channel_name
    )
    VALUES (
        p_guild_id, p_user_id, p_username, p_activity_type,
        p_activity_details, p_channel_id, p_channel_name
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_feature_analytics(
    p_guild_id VARCHAR(20),
    p_feature_name VARCHAR(50),
    p_user_id VARCHAR(20)
)
RETURNS VOID AS $$
DECLARE
    current_users JSON;
    updated_users JSON;
BEGIN
    -- Get current unique users array
    SELECT unique_users INTO current_users
    FROM feature_analytics 
    WHERE guild_id = p_guild_id 
      AND feature_name = p_feature_name 
      AND usage_date = CURRENT_DATE;
    
    -- If no record exists, create one
    IF current_users IS NULL THEN
        INSERT INTO feature_analytics (guild_id, feature_name, usage_count, unique_users)
        VALUES (p_guild_id, p_feature_name, 1, JSON_BUILD_ARRAY(p_user_id));
    ELSE
        -- Check if user is already in the array
        IF NOT (current_users ? p_user_id) THEN
            -- Add user to array
            updated_users := JSON_BUILD_ARRAY(p_user_id) || current_users;
        ELSE
            updated_users := current_users;
        END IF;
        
        -- Update the record
        UPDATE feature_analytics 
        SET usage_count = usage_count + 1,
            unique_users = updated_users,
            last_used = CURRENT_TIMESTAMP
        WHERE guild_id = p_guild_id 
          AND feature_name = p_feature_name 
          AND usage_date = CURRENT_DATE;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS VOID AS $$
BEGIN
    -- Delete old user activity (keep 90 days)
    DELETE FROM user_activity 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '90 days';
    
    -- Delete old error logs (keep 30 days)
    DELETE FROM error_logs 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '30 days';
    
    -- Delete old feature analytics (keep 1 year)
    DELETE FROM feature_analytics 
    WHERE usage_date < CURRENT_DATE - INTERVAL '1 year';
    
    -- Delete sent notifications older than 7 days
    DELETE FROM system_notifications 
    WHERE is_sent = true 
      AND sent_date < CURRENT_TIMESTAMP - INTERVAL '7 days';
    
    -- Archive old audit logs (keep 6 months)
    DELETE FROM audit_log 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '6 months';
    
    RAISE NOTICE 'Cleanup completed: removed old activity, error logs, and analytics data';
END;
$$ LANGUAGE plpgsql;

-- Insert scheduled cleanup task for all guilds
INSERT INTO scheduled_tasks (guild_id, task_type, task_name, task_data, scheduled_time, repeat_interval, next_run)
SELECT DISTINCT 
    guild_id,
    'cleanup_old_data',
    'Daily Data Cleanup',
    '{"tables": ["user_activity", "error_logs", "feature_analytics", "system_notifications", "audit_log"]}',
    CURRENT_TIMESTAMP + INTERVAL '1 day',
    'daily',
    CURRENT_TIMESTAMP + INTERVAL '1 day'
FROM guilds
ON CONFLICT DO NOTHING;