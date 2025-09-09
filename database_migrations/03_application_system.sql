-- Migration: Organization Application System for /red-join subcommands
-- Date: September 8, 2025
-- Purpose: Support organization recruitment workflow with applications, reviews, and approvals

-- Applications table
CREATE TABLE IF NOT EXISTS applications (
    application_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    applicant_id VARCHAR(20),
    applicant_name VARCHAR(100),
    applicant_discriminator VARCHAR(10),
    application_uid VARCHAR(50) UNIQUE NOT NULL, -- Format: RL20250908001
    
    -- Application details
    position_applied VARCHAR(50) NOT NULL,
    sc_handle VARCHAR(100),
    gaming_experience TEXT,
    why_join_reason TEXT,
    availability_info TEXT,
    additional_info TEXT,
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'reviewing', 'interview_scheduled', 'approved', 'denied', 'withdrawn')),
    priority VARCHAR(10) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    
    -- Workflow tracking
    submitted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by_id VARCHAR(20),
    reviewed_by_name VARCHAR(100),
    review_started_date TIMESTAMP,
    decision_date TIMESTAMP,
    decision_by_id VARCHAR(20),
    decision_by_name VARCHAR(100),
    decision_reason TEXT,
    decision_notes TEXT,
    
    -- Interview scheduling
    interview_scheduled_date TIMESTAMP,
    interview_scheduled_by_id VARCHAR(20),
    interview_scheduled_by_name VARCHAR(100),
    interview_notes TEXT,
    
    -- Approval/Denial
    approval_notes TEXT,
    denial_reason TEXT,
    
    -- Role assignment (for approved applications)
    assigned_roles JSON,
    welcome_message_sent BOOLEAN DEFAULT FALSE,
    onboarding_completed BOOLEAN DEFAULT FALSE
);

-- Application review history
CREATE TABLE IF NOT EXISTS application_reviews (
    review_id SERIAL PRIMARY KEY,
    application_id INTEGER REFERENCES applications(application_id) ON DELETE CASCADE,
    reviewer_id VARCHAR(20),
    reviewer_name VARCHAR(100),
    review_action VARCHAR(20) NOT NULL CHECK (review_action IN ('started_review', 'added_notes', 'scheduled_interview', 'approved', 'denied', 'requested_changes')),
    review_notes TEXT,
    previous_status VARCHAR(20),
    new_status VARCHAR(20),
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Application positions/roles lookup
CREATE TABLE IF NOT EXISTS application_positions (
    position_id SERIAL PRIMARY KEY,
    position_name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    requirements TEXT,
    auto_assign_roles JSON, -- Array of role IDs to assign upon approval
    requires_interview BOOLEAN DEFAULT FALSE,
    approval_level VARCHAR(20) DEFAULT 'officer' CHECK (approval_level IN ('officer', 'admin', 'leadership')),
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Application settings per guild
CREATE TABLE IF NOT EXISTS application_settings (
    setting_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    auto_role_assignment BOOLEAN DEFAULT TRUE,
    welcome_channel_id VARCHAR(20),
    recruitment_channel_id VARCHAR(20),
    officer_notification_role_id VARCHAR(20),
    auto_interview_required BOOLEAN DEFAULT FALSE,
    max_pending_days INTEGER DEFAULT 30, -- Auto-archive applications after X days
    application_cooldown_days INTEGER DEFAULT 7, -- Prevent reapplication for X days
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id)
);

-- Application notifications/reminders
CREATE TABLE IF NOT EXISTS application_notifications (
    notification_id SERIAL PRIMARY KEY,
    application_id INTEGER REFERENCES applications(application_id) ON DELETE CASCADE,
    notification_type VARCHAR(30) NOT NULL CHECK (notification_type IN ('submitted', 'review_started', 'interview_scheduled', 'approved', 'denied', 'reminder')),
    recipient_id VARCHAR(20),
    recipient_name VARCHAR(100),
    message_content TEXT,
    sent_date TIMESTAMP,
    is_sent BOOLEAN DEFAULT FALSE,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for application operations
CREATE INDEX IF NOT EXISTS idx_applications_guild ON applications(guild_id);
CREATE INDEX IF NOT EXISTS idx_applications_applicant ON applications(applicant_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_position ON applications(position_applied);
CREATE INDEX IF NOT EXISTS idx_applications_submitted ON applications(submitted_date);
CREATE INDEX IF NOT EXISTS idx_applications_uid ON applications(application_uid);
CREATE INDEX IF NOT EXISTS idx_applications_reviewer ON applications(reviewed_by_id);

CREATE INDEX IF NOT EXISTS idx_application_reviews_application ON application_reviews(application_id);
CREATE INDEX IF NOT EXISTS idx_application_reviews_reviewer ON application_reviews(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_application_reviews_action ON application_reviews(review_action);
CREATE INDEX IF NOT EXISTS idx_application_reviews_date ON application_reviews(review_date);
CREATE INDEX IF NOT EXISTS idx_application_reviews_guild ON application_reviews(guild_id);

CREATE INDEX IF NOT EXISTS idx_application_notifications_application ON application_notifications(application_id);
CREATE INDEX IF NOT EXISTS idx_application_notifications_type ON application_notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_application_notifications_sent ON application_notifications(is_sent);
CREATE INDEX IF NOT EXISTS idx_application_notifications_guild ON application_notifications(guild_id);

-- Insert standard application positions
INSERT INTO application_positions (position_name, display_name, description, requires_interview, approval_level, sort_order) 
VALUES 
    ('general', 'General Member', 'Standard organization membership with basic privileges', false, 'officer', 1),
    ('pilot', 'Pilot', 'Combat and transport pilot specialization', true, 'officer', 2),
    ('engineer', 'Engineer', 'Ship and station maintenance specialist', true, 'officer', 3),
    ('trader', 'Trader', 'Commerce and trading operations specialist', false, 'officer', 4),
    ('security', 'Security Officer', 'Defense and escort operations specialist', true, 'admin', 5),
    ('medic', 'Medical Officer', 'Medical and rescue operations specialist', true, 'officer', 6),
    ('specialist', 'Specialist Role', 'Custom specialist positions (leadership discretion)', true, 'leadership', 7)
ON CONFLICT (position_name) DO NOTHING;

-- Create views for application management
CREATE OR REPLACE VIEW pending_applications AS
SELECT 
    a.application_id,
    a.application_uid,
    a.guild_id,
    a.applicant_name,
    a.position_applied,
    ap.display_name as position_display,
    a.sc_handle,
    a.status,
    a.priority,
    a.submitted_date,
    a.last_updated,
    a.reviewed_by_name,
    EXTRACT(days FROM (CURRENT_TIMESTAMP - a.submitted_date)) as days_pending,
    ap.requires_interview,
    ap.approval_level
FROM applications a
LEFT JOIN application_positions ap ON a.position_applied = ap.position_name
WHERE a.status IN ('pending', 'reviewing', 'interview_scheduled')
ORDER BY a.priority DESC, a.submitted_date ASC;

CREATE OR REPLACE VIEW application_statistics AS
SELECT 
    a.guild_id,
    COUNT(*) as total_applications,
    COUNT(*) FILTER (WHERE a.status = 'pending') as pending_count,
    COUNT(*) FILTER (WHERE a.status = 'reviewing') as reviewing_count,
    COUNT(*) FILTER (WHERE a.status = 'interview_scheduled') as interview_scheduled_count,
    COUNT(*) FILTER (WHERE a.status = 'approved') as approved_count,
    COUNT(*) FILTER (WHERE a.status = 'denied') as denied_count,
    COUNT(*) FILTER (WHERE a.status = 'withdrawn') as withdrawn_count,
    COUNT(*) FILTER (WHERE a.submitted_date >= CURRENT_DATE - INTERVAL '30 days') as applications_last_30_days,
    COUNT(*) FILTER (WHERE a.submitted_date >= CURRENT_DATE - INTERVAL '7 days') as applications_last_7_days,
    AVG(EXTRACT(days FROM (a.decision_date - a.submitted_date))) FILTER (WHERE a.decision_date IS NOT NULL) as avg_processing_days
FROM applications a
GROUP BY a.guild_id;

-- Insert default application settings for existing guilds
INSERT INTO application_settings (guild_id, auto_role_assignment, auto_interview_required, max_pending_days)
SELECT DISTINCT guild_id, true, false, 30
FROM guilds
ON CONFLICT (guild_id) DO NOTHING;

-- Function to generate unique application UIDs
CREATE OR REPLACE FUNCTION generate_application_uid()
RETURNS TEXT AS $$
DECLARE
    new_uid TEXT;
    uid_exists BOOLEAN;
BEGIN
    LOOP
        -- Generate UID in format: RL + YYYYMMDD + 3-digit random number
        new_uid := 'RL' || TO_CHAR(CURRENT_DATE, 'YYYYMMDD') || LPAD(FLOOR(RANDOM() * 1000)::TEXT, 3, '0');
        
        -- Check if this UID already exists
        SELECT EXISTS(SELECT 1 FROM applications WHERE application_uid = new_uid) INTO uid_exists;
        
        -- If it doesn't exist, we can use it
        IF NOT uid_exists THEN
            RETURN new_uid;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-generate application UID
CREATE OR REPLACE FUNCTION set_application_uid()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.application_uid IS NULL OR NEW.application_uid = '' THEN
        NEW.application_uid := generate_application_uid();
    END IF;
    NEW.last_updated := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_set_application_uid ON applications;
CREATE TRIGGER trigger_set_application_uid
    BEFORE INSERT ON applications
    FOR EACH ROW
    EXECUTE FUNCTION set_application_uid();

-- Trigger to update last_updated timestamp
DROP TRIGGER IF EXISTS trigger_update_application_timestamp ON applications;
CREATE TRIGGER trigger_update_application_timestamp
    BEFORE UPDATE ON applications
    FOR EACH ROW
    EXECUTE FUNCTION set_application_uid();