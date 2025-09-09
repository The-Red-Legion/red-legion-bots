-- ==================================================================
-- RED LEGION DISCORD BOT - COMPLETE DATABASE SCHEMA
-- ==================================================================
-- Generated: $(date)
-- Purpose: Complete schema for Red Legion Discord Bot database
-- Includes: Existing tables + Missing migration tables
-- ==================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ==================================================================
-- CORE FOUNDATION TABLES (Must be created first for foreign keys)
-- ==================================================================

-- User management (comprehensive) - MUST BE FIRST for foreign key references
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(20) PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    display_name VARCHAR(100),
    first_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================================================================
-- EXISTING TABLES (Currently in database)
-- ==================================================================

-- Core guild/server management
CREATE TABLE IF NOT EXISTS guilds (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    settings JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Guild membership tracking
CREATE TABLE IF NOT EXISTS guild_memberships (
    guild_id BIGINT NOT NULL REFERENCES guilds(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    is_org_member BOOLEAN DEFAULT false,
    join_date TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (guild_id, user_id)
);

-- Mining channel configuration
CREATE TABLE IF NOT EXISTS mining_channels (
    id INTEGER PRIMARY KEY DEFAULT nextval('mining_channels_id_seq'::regclass),
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    channel_id BIGINT NOT NULL UNIQUE,
    channel_name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Mining events (Sunday mining, etc.)
CREATE TABLE IF NOT EXISTS mining_events (
    id INTEGER PRIMARY KEY DEFAULT nextval('mining_events_id_seq'::regclass),
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    event_date DATE NOT NULL,
    event_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    event_name TEXT DEFAULT 'Sunday Mining'::text,
    status VARCHAR(20) DEFAULT 'planned'::character varying 
        CHECK (status IN ('planned', 'active', 'completed', 'cancelled')),
    total_participants INTEGER DEFAULT 0,
    total_value_auec NUMERIC(15,2) DEFAULT 0,
    payroll_processed BOOLEAN DEFAULT false,
    pdf_generated BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Event tracking (legacy compatibility)
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY DEFAULT nextval('events_id_seq'::regclass),
    guild_id BIGINT NOT NULL REFERENCES guilds(id) ON DELETE CASCADE,
    event_date DATE NOT NULL,
    event_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    event_name TEXT DEFAULT 'Sunday Mining'::text,
    total_participants INTEGER DEFAULT 0,
    total_payout REAL,
    is_open BOOLEAN DEFAULT true,
    payroll_calculated BOOLEAN DEFAULT false,
    pdf_generated BOOLEAN DEFAULT false,
    event_id INTEGER,
    channel_id TEXT,
    channel_name TEXT,
    start_time TEXT,
    end_time TEXT,
    total_value REAL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Mining participation tracking
CREATE TABLE IF NOT EXISTS mining_participation (
    id INTEGER PRIMARY KEY DEFAULT nextval('mining_participation_id_seq'::regclass),
    event_id INTEGER REFERENCES mining_events(id) ON DELETE CASCADE,
    user_id BIGINT,
    channel_id BIGINT,
    session_start TIMESTAMP WITHOUT TIME ZONE,
    session_end TIMESTAMP WITHOUT TIME ZONE,
    duration_seconds INTEGER,
    is_org_member BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    member_id TEXT,
    username TEXT,
    start_time TIMESTAMP WITHOUT TIME ZONE,
    end_time TIMESTAMP WITHOUT TIME ZONE,
    total_time_minutes INTEGER
);

-- Materials and ore types
CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY DEFAULT nextval('materials_id_seq'::regclass),
    name TEXT NOT NULL UNIQUE,
    category VARCHAR(50) CHECK (category IN ('ore', 'refined', 'component', 'commodity')),
    base_value_auec NUMERIC(10,2),
    current_market_value NUMERIC(10,2),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Mining yields/hauls
CREATE TABLE IF NOT EXISTS mining_yields (
    id INTEGER PRIMARY KEY DEFAULT nextval('mining_yields_id_seq'::regclass),
    participation_id INTEGER REFERENCES mining_participation(id) ON DELETE CASCADE,
    material_id INTEGER REFERENCES materials(id) ON DELETE CASCADE,
    quantity_scu NUMERIC(10,2) NOT NULL,
    estimated_value NUMERIC(15,2),
    recorded_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Loan system
CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY DEFAULT nextval('loans_id_seq'::regclass),
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    borrower_id BIGINT,
    amount_auec NUMERIC(15,2) NOT NULL,
    interest_rate NUMERIC(5,4) DEFAULT 0.0000,
    status VARCHAR(20) DEFAULT 'active'::character varying
        CHECK (status IN ('pending', 'approved', 'denied', 'active', 'completed', 'defaulted')),
    issued_date TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP WITHOUT TIME ZONE,
    paid_date TIMESTAMP WITHOUT TIME ZONE
);

-- ==================================================================
-- MISSING TABLES (From migrations but not in database)
-- ==================================================================

-- Enhanced loan system
CREATE TABLE IF NOT EXISTS loan_payments (
    payment_id SERIAL PRIMARY KEY,
    loan_id INTEGER REFERENCES loans(id) ON DELETE CASCADE,
    payment_amount DECIMAL(15,2) NOT NULL,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_method VARCHAR(50),
    transaction_reference VARCHAR(100),
    notes TEXT,
    recorded_by VARCHAR(20) REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loan_reminders (
    reminder_id SERIAL PRIMARY KEY,
    loan_id INTEGER REFERENCES loans(id) ON DELETE CASCADE,
    reminder_date TIMESTAMP NOT NULL,
    reminder_type VARCHAR(20) DEFAULT 'payment_due' CHECK (reminder_type IN ('payment_due', 'overdue', 'final_notice')),
    sent_date TIMESTAMP,
    is_sent BOOLEAN DEFAULT FALSE,
    message_content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loan_settings (
    guild_id BIGINT PRIMARY KEY REFERENCES guilds(id) ON DELETE CASCADE,
    default_interest_rate DECIMAL(5,4) DEFAULT 0.0500,
    max_loan_amount DECIMAL(15,2) DEFAULT 100000.00,
    default_loan_term_days INTEGER DEFAULT 30,
    require_collateral BOOLEAN DEFAULT FALSE,
    auto_approve_limit DECIMAL(15,2) DEFAULT 0.00,
    reminder_days_before INTEGER[] DEFAULT ARRAY[7, 3, 1],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Market system
CREATE TABLE IF NOT EXISTS market_listings (
    listing_id SERIAL PRIMARY KEY,
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    seller_id VARCHAR(20) REFERENCES users(user_id),
    seller_name VARCHAR(100) NOT NULL,
    item_name VARCHAR(200) NOT NULL,
    category_id INTEGER,
    quantity INTEGER DEFAULT 1,
    unit_price DECIMAL(15,2) NOT NULL,
    total_price DECIMAL(15,2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    currency VARCHAR(10) DEFAULT 'aUEC',
    description TEXT,
    location VARCHAR(200),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'sold', 'cancelled', 'expired')),
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS market_categories (
    category_id SERIAL PRIMARY KEY,
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_category_id INTEGER REFERENCES market_categories(category_id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS market_transactions (
    transaction_id SERIAL PRIMARY KEY,
    listing_id INTEGER REFERENCES market_listings(listing_id) ON DELETE CASCADE,
    buyer_id VARCHAR(20) REFERENCES users(user_id),
    buyer_name VARCHAR(100) NOT NULL,
    quantity_sold INTEGER NOT NULL,
    unit_price DECIMAL(15,2) NOT NULL,
    total_amount DECIMAL(15,2) NOT NULL,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_method VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS market_favorites (
    favorite_id SERIAL PRIMARY KEY,
    user_id VARCHAR(20) REFERENCES users(user_id) ON DELETE CASCADE,
    listing_id INTEGER REFERENCES market_listings(listing_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, listing_id)
);

CREATE TABLE IF NOT EXISTS market_reputation (
    reputation_id SERIAL PRIMARY KEY,
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    user_id VARCHAR(20) REFERENCES users(user_id) ON DELETE CASCADE,
    transaction_id INTEGER REFERENCES market_transactions(transaction_id),
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    feedback TEXT,
    is_seller BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS market_settings (
    guild_id BIGINT PRIMARY KEY REFERENCES guilds(id) ON DELETE CASCADE,
    commission_rate DECIMAL(5,4) DEFAULT 0.0000,
    max_listing_duration_days INTEGER DEFAULT 30,
    require_reputation_threshold INTEGER DEFAULT 0,
    auto_expire_listings BOOLEAN DEFAULT TRUE,
    allow_external_sales BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Application system
CREATE TABLE IF NOT EXISTS applications (
    application_id SERIAL PRIMARY KEY,
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    applicant_id VARCHAR(20) REFERENCES users(user_id),
    applicant_name VARCHAR(100) NOT NULL,
    position_id INTEGER,
    application_type VARCHAR(50) DEFAULT 'membership',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'under_review', 'approved', 'denied', 'withdrawn')),
    submitted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_date TIMESTAMP,
    reviewer_id VARCHAR(20) REFERENCES users(user_id),
    priority INTEGER DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
    application_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS application_positions (
    position_id SERIAL PRIMARY KEY,
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    position_name VARCHAR(100) NOT NULL,
    description TEXT,
    requirements TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    auto_assign_role_id VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS application_reviews (
    review_id SERIAL PRIMARY KEY,
    application_id INTEGER REFERENCES applications(application_id) ON DELETE CASCADE,
    reviewer_id VARCHAR(20) REFERENCES users(user_id),
    review_type VARCHAR(20) DEFAULT 'interview' CHECK (review_type IN ('background', 'interview', 'skills', 'final')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'passed', 'failed', 'scheduled')),
    notes TEXT,
    scheduled_date TIMESTAMP,
    completed_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS application_notifications (
    notification_id SERIAL PRIMARY KEY,
    application_id INTEGER REFERENCES applications(application_id) ON DELETE CASCADE,
    recipient_id VARCHAR(20) REFERENCES users(user_id),
    notification_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    is_sent BOOLEAN DEFAULT FALSE,
    sent_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS application_settings (
    guild_id BIGINT PRIMARY KEY REFERENCES guilds(id) ON DELETE CASCADE,
    auto_acknowledge BOOLEAN DEFAULT TRUE,
    require_background_check BOOLEAN DEFAULT FALSE,
    interview_required BOOLEAN DEFAULT TRUE,
    notification_channel_id VARCHAR(20),
    reviewer_role_id VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System tables
CREATE TABLE IF NOT EXISTS command_usage (
    usage_id SERIAL PRIMARY KEY,
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    user_id VARCHAR(20) REFERENCES users(user_id),
    command_name VARCHAR(100) NOT NULL,
    command_type VARCHAR(20) DEFAULT 'slash',
    success BOOLEAN DEFAULT TRUE,
    execution_time_ms INTEGER,
    error_message TEXT,
    parameters JSONB,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id SERIAL PRIMARY KEY,
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    user_id VARCHAR(20) REFERENCES users(user_id),
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50),
    target_id VARCHAR(50),
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS error_logs (
    error_id SERIAL PRIMARY KEY,
    guild_id BIGINT REFERENCES guilds(id),
    user_id VARCHAR(20) REFERENCES users(user_id),
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    command_context TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bot_config (
    config_id SERIAL PRIMARY KEY,
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    config_key VARCHAR(100) NOT NULL,
    config_value TEXT,
    data_type VARCHAR(20) DEFAULT 'string' CHECK (data_type IN ('string', 'integer', 'boolean', 'json')),
    description TEXT,
    is_encrypted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, config_key)
);

CREATE TABLE IF NOT EXISTS user_preferences (
    preference_id SERIAL PRIMARY KEY,
    user_id VARCHAR(20) REFERENCES users(user_id) ON DELETE CASCADE,
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    preference_key VARCHAR(100) NOT NULL,
    preference_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, guild_id, preference_key)
);

CREATE TABLE IF NOT EXISTS user_activity (
    activity_id SERIAL PRIMARY KEY,
    user_id VARCHAR(20) REFERENCES users(user_id) ON DELETE CASCADE,
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL,
    activity_data JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS system_notifications (
    notification_id SERIAL PRIMARY KEY,
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    priority INTEGER DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
    target_users VARCHAR(20)[] DEFAULT ARRAY[]::VARCHAR(20)[],
    target_roles VARCHAR(20)[] DEFAULT ARRAY[]::VARCHAR(20)[],
    is_sent BOOLEAN DEFAULT FALSE,
    send_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS system_metrics (
    metric_id SERIAL PRIMARY KEY,
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    metric_unit VARCHAR(20),
    tags JSONB DEFAULT '{}',
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feature_analytics (
    analytics_id SERIAL PRIMARY KEY,
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    feature_name VARCHAR(100) NOT NULL,
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    user_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, feature_name)
);

CREATE TABLE IF NOT EXISTS scheduled_tasks (
    task_id SERIAL PRIMARY KEY,
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    task_name VARCHAR(100) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    cron_expression VARCHAR(100),
    next_run TIMESTAMP NOT NULL,
    last_run TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    max_retries INTEGER DEFAULT 3,
    retry_count INTEGER DEFAULT 0,
    task_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS adhoc_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    creator_id VARCHAR(50) NOT NULL,
    guild_id VARCHAR(50) NOT NULL,
    channel_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================================================================
-- INDEXES FOR PERFORMANCE
-- ==================================================================

-- Core table indexes
CREATE INDEX IF NOT EXISTS idx_guilds_active ON guilds(created_at) WHERE updated_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_guild_memberships_org_member ON guild_memberships(guild_id, is_org_member);
CREATE INDEX IF NOT EXISTS idx_guild_memberships_user_lookup ON guild_memberships(user_id);

-- Mining-related indexes
CREATE INDEX IF NOT EXISTS idx_mining_channels_guild_active ON mining_channels(guild_id, is_active);
CREATE INDEX IF NOT EXISTS idx_mining_events_guild_date ON mining_events(guild_id, event_date);
CREATE INDEX IF NOT EXISTS idx_mining_events_status ON mining_events(guild_id, status);
CREATE INDEX IF NOT EXISTS idx_mining_participation_event ON mining_participation(event_id);
CREATE INDEX IF NOT EXISTS idx_mining_participation_user ON mining_participation(user_id);
CREATE INDEX IF NOT EXISTS idx_mining_participation_session ON mining_participation(session_start, session_end);

-- Events and legacy compatibility
CREATE INDEX IF NOT EXISTS idx_events_guild_date ON events(guild_id, event_date);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(is_open, payroll_calculated);

-- Materials and yields
CREATE INDEX IF NOT EXISTS idx_materials_name ON materials(name);
CREATE INDEX IF NOT EXISTS idx_materials_category ON materials(category);
CREATE INDEX IF NOT EXISTS idx_mining_yields_participation ON mining_yields(participation_id);

-- Loan system indexes
CREATE INDEX IF NOT EXISTS idx_loans_guild_borrower ON loans(guild_id, borrower_id);
CREATE INDEX IF NOT EXISTS idx_loans_status ON loans(status);
CREATE INDEX IF NOT EXISTS idx_loans_due_date ON loans(due_date) WHERE due_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_loan_payments_loan ON loan_payments(loan_id);
CREATE INDEX IF NOT EXISTS idx_loan_reminders_loan_date ON loan_reminders(loan_id, reminder_date);

-- Market system indexes
CREATE INDEX IF NOT EXISTS idx_market_listings_guild_status ON market_listings(guild_id, status);
CREATE INDEX IF NOT EXISTS idx_market_listings_seller ON market_listings(seller_id);
CREATE INDEX IF NOT EXISTS idx_market_listings_category ON market_listings(category_id);
CREATE INDEX IF NOT EXISTS idx_market_listings_expires ON market_listings(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_market_transactions_listing ON market_transactions(listing_id);

-- User and activity indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_command_usage_guild_command ON command_usage(guild_id, command_name);
CREATE INDEX IF NOT EXISTS idx_command_usage_user ON command_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_command_usage_date ON command_usage(used_at);

-- Application system indexes
CREATE INDEX IF NOT EXISTS idx_applications_guild_status ON applications(guild_id, status);
CREATE INDEX IF NOT EXISTS idx_applications_applicant ON applications(applicant_id);
CREATE INDEX IF NOT EXISTS idx_application_reviews_application ON application_reviews(application_id);

-- System indexes
CREATE INDEX IF NOT EXISTS idx_audit_log_guild_date ON audit_log(guild_id, created_at);
CREATE INDEX IF NOT EXISTS idx_error_logs_guild_resolved ON error_logs(guild_id, resolved);
CREATE INDEX IF NOT EXISTS idx_system_notifications_guild_sent ON system_notifications(guild_id, is_sent);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_next_run ON scheduled_tasks(next_run, is_active);

-- ==================================================================
-- TRIGGERS AND FUNCTIONS
-- ==================================================================

-- Auto-update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update triggers to relevant tables
CREATE TRIGGER trigger_guilds_updated_at
    BEFORE UPDATE ON guilds
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_mining_events_updated_at
    BEFORE UPDATE ON mining_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_events_updated_at
    BEFORE UPDATE ON events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_market_listings_updated_at
    BEFORE UPDATE ON market_listings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_applications_updated_at
    BEFORE UPDATE ON applications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_bot_config_updated_at
    BEFORE UPDATE ON bot_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ==================================================================
-- DEFAULT DATA INSERTS
-- ==================================================================

-- Insert default materials
INSERT INTO materials (name, category, base_value_auec, current_market_value) VALUES
    ('Quantainium', 'ore', 8.8, 8.8),
    ('Bexalite', 'ore', 5.5, 5.5),
    ('Taranite', 'ore', 4.5, 4.5),
    ('Laranite', 'ore', 3.5, 3.5),
    ('Borase', 'ore', 2.8, 2.8),
    ('Hadanite', 'ore', 2.5, 2.5),
    ('Titanium', 'ore', 2.2, 2.2),
    ('Diamond', 'ore', 7.2, 7.2),
    ('Gold', 'ore', 6.1, 6.1),
    ('Copper', 'ore', 1.5, 1.5),
    ('Stileron', 'ore', 2.0, 2.0),
    ('Riccite', 'ore', 3.2, 3.2),
    ('Agricium', 'ore', 2.7, 2.7),
    ('Hephaestanite', 'ore', 3.8, 3.8),
    ('Tungsten', 'ore', 2.1, 2.1),
    ('Iron', 'ore', 1.2, 1.2),
    ('Quartz', 'ore', 1.8, 1.8),
    ('Corundum', 'ore', 2.3, 2.3),
    ('Tin', 'ore', 1.4, 1.4),
    ('Aluminum', 'ore', 1.3, 1.3),
    ('Silicon', 'ore', 1.6, 1.6),
    ('Beryl', 'ore', 2.6, 2.6)
ON CONFLICT (name) DO NOTHING;

-- ==================================================================
-- VIEWS FOR COMMON QUERIES
-- ==================================================================

-- Active mining events view
CREATE OR REPLACE VIEW active_mining_events AS
SELECT 
    me.*,
    g.name as guild_name,
    COUNT(mp.id) as current_participants
FROM mining_events me
LEFT JOIN guilds g ON me.guild_id = g.id
LEFT JOIN mining_participation mp ON me.id = mp.event_id
WHERE me.status IN ('planned', 'active')
GROUP BY me.id, g.name;

-- User participation summary view
CREATE OR REPLACE VIEW user_participation_summary AS
SELECT 
    mp.user_id,
    mp.username,
    COUNT(DISTINCT mp.event_id) as events_participated,
    SUM(mp.duration_seconds) as total_seconds,
    SUM(mp.total_time_minutes) as total_minutes,
    AVG(mp.duration_seconds) as avg_session_seconds,
    MAX(mp.session_end) as last_participation
FROM mining_participation mp
WHERE mp.session_end IS NOT NULL
GROUP BY mp.user_id, mp.username;

-- Market listings with seller info view
CREATE OR REPLACE VIEW market_listings_detail AS
SELECT 
    ml.*,
    u.username as seller_username,
    mc.name as category_name,
    CASE 
        WHEN ml.expires_at < CURRENT_TIMESTAMP THEN 'expired'
        ELSE ml.status 
    END as effective_status
FROM market_listings ml
LEFT JOIN users u ON ml.seller_id = u.user_id
LEFT JOIN market_categories mc ON ml.category_id = mc.category_id;

-- ==================================================================
-- COMMENTS FOR DOCUMENTATION
-- ==================================================================

COMMENT ON TABLE guilds IS 'Discord servers/guilds using the bot';
COMMENT ON TABLE guild_memberships IS 'User membership in Discord guilds';
COMMENT ON TABLE mining_channels IS 'Approved voice channels for mining operations';
COMMENT ON TABLE mining_events IS 'Scheduled and completed mining events';
COMMENT ON TABLE events IS 'Legacy events table for backward compatibility';
COMMENT ON TABLE mining_participation IS 'Individual user participation in mining events';
COMMENT ON TABLE materials IS 'Star Citizen ore types and materials with market values';
COMMENT ON TABLE mining_yields IS 'Materials harvested during mining sessions';
COMMENT ON TABLE loans IS 'Member-to-member loans and organization loans';
COMMENT ON TABLE users IS 'Discord users interacting with the bot';
COMMENT ON TABLE market_listings IS 'Community marketplace item listings';
COMMENT ON TABLE applications IS 'Organization membership and position applications';

-- ==================================================================
-- SCHEMA METADATA
-- ==================================================================

INSERT INTO schema_metadata (version, description) VALUES 
    ('2.0.0', 'Complete Red Legion Bot Schema - Generated from migration analysis')
ON CONFLICT (version) DO UPDATE SET 
    description = EXCLUDED.description,
    applied_at = CURRENT_TIMESTAMP;

-- ==================================================================
-- END OF SCHEMA
-- ==================================================================