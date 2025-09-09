-- Migration: Foundation Schema - Core Database Tables
-- Date: September 8, 2025
-- Purpose: Establish core database structure for Red Legion Bot

-- Users table - Core user information
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

-- Guilds table - Discord servers
CREATE TABLE IF NOT EXISTS guilds (
    guild_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    owner_id VARCHAR(20),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Guild memberships table - User membership in guilds
CREATE TABLE IF NOT EXISTS guild_memberships (
    membership_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    user_id VARCHAR(20) REFERENCES users(user_id),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    roles TEXT[],
    nickname VARCHAR(100),
    is_org_member BOOLEAN DEFAULT FALSE,
    UNIQUE(guild_id, user_id)
);

-- Mining channels table - Approved voice channels for mining
CREATE TABLE IF NOT EXISTS mining_channels (
    channel_id VARCHAR(20) PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    channel_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mining events table - Sunday mining and adhoc events
CREATE TABLE IF NOT EXISTS mining_events (
    id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    event_date DATE NOT NULL,
    event_time TIMESTAMP NOT NULL,
    event_name TEXT DEFAULT 'Sunday Mining',
    event_type VARCHAR(50) DEFAULT 'mining',
    status VARCHAR(20) DEFAULT 'planned' CHECK (status IN ('planned', 'active', 'completed', 'cancelled')),
    organizer_id VARCHAR(20),
    organizer_name VARCHAR(100),
    location VARCHAR(200),
    description TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    total_participants INTEGER DEFAULT 0,
    total_value_auec DECIMAL(15,2) DEFAULT 0,
    total_payout DECIMAL(15,2),
    payroll_calculated BOOLEAN DEFAULT FALSE,
    payroll_processed BOOLEAN DEFAULT FALSE,
    pdf_generated BOOLEAN DEFAULT FALSE,
    is_open BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alternative table name for compatibility
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    event_date DATE NOT NULL,
    event_time TIMESTAMP NOT NULL,
    total_participants INTEGER DEFAULT 0,
    total_payout DECIMAL(15,2),
    is_open BOOLEAN DEFAULT FALSE,
    payroll_calculated BOOLEAN DEFAULT FALSE,
    pdf_generated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mining participation tracking
CREATE TABLE IF NOT EXISTS mining_participation (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES mining_events(id) ON DELETE CASCADE,
    member_id VARCHAR(20),
    user_id VARCHAR(20) REFERENCES users(user_id),
    username VARCHAR(100),
    channel_id VARCHAR(20),
    channel_name VARCHAR(100),
    session_start TIMESTAMP NOT NULL,
    session_end TIMESTAMP,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    session_duration INTEGER,
    total_session_time INTEGER,
    primary_channel_id VARCHAR(20),
    is_org_member BOOLEAN DEFAULT FALSE,
    is_valid BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Basic loans table (will be enhanced in 02_enhanced_loan_system.sql)
CREATE TABLE IF NOT EXISTS loans (
    loan_id SERIAL PRIMARY KEY,
    id SERIAL UNIQUE, -- For compatibility
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    borrower_id VARCHAR(20),
    borrower_name VARCHAR(100),
    amount DECIMAL(15,2) NOT NULL,
    amount_auec DECIMAL(15,2), -- For compatibility
    interest_rate DECIMAL(5,4) DEFAULT 0.0000,
    purpose TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'denied', 'active', 'completed', 'defaulted')),
    issued_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP,
    paid_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Materials and their current values
CREATE TABLE IF NOT EXISTS materials (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    category VARCHAR(50) CHECK (category IN ('ore', 'refined', 'component', 'commodity')),
    base_value_auec DECIMAL(10,2),
    current_market_value DECIMAL(10,2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mining session material yields
CREATE TABLE IF NOT EXISTS mining_yields (
    id SERIAL PRIMARY KEY,
    participation_id INTEGER REFERENCES mining_participation(id) ON DELETE CASCADE,
    material_id INTEGER REFERENCES materials(id) ON DELETE CASCADE,
    quantity_scu DECIMAL(10,2) NOT NULL,
    estimated_value DECIMAL(15,2),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Command usage tracking for analytics
CREATE TABLE IF NOT EXISTS command_usage (
    usage_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    user_id VARCHAR(20) REFERENCES users(user_id),
    command_name VARCHAR(100) NOT NULL,
    command_type VARCHAR(20) DEFAULT 'slash', -- slash, prefix, context
    success BOOLEAN DEFAULT TRUE,
    execution_time_ms INTEGER,
    error_message TEXT,
    parameters JSON,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Adhoc session support
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

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

CREATE INDEX IF NOT EXISTS idx_guilds_owner ON guilds(owner_id);
CREATE INDEX IF NOT EXISTS idx_guilds_active ON guilds(is_active);

CREATE INDEX IF NOT EXISTS idx_guild_memberships_guild_id ON guild_memberships(guild_id);
CREATE INDEX IF NOT EXISTS idx_guild_memberships_user_id ON guild_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_guild_memberships_org_member ON guild_memberships(guild_id, is_org_member);
CREATE INDEX IF NOT EXISTS idx_guild_memberships_active ON guild_memberships(is_active);

CREATE INDEX IF NOT EXISTS idx_mining_channels_guild ON mining_channels(guild_id);
CREATE INDEX IF NOT EXISTS idx_mining_channels_active ON mining_channels(is_active);

CREATE INDEX IF NOT EXISTS idx_mining_events_guild_date ON mining_events(guild_id, event_date);
CREATE INDEX IF NOT EXISTS idx_mining_events_status ON mining_events(guild_id, status);
CREATE INDEX IF NOT EXISTS idx_mining_events_organizer ON mining_events(organizer_id);
CREATE INDEX IF NOT EXISTS idx_mining_events_type ON mining_events(event_type);

CREATE INDEX IF NOT EXISTS idx_events_guild ON events(guild_id);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);
CREATE INDEX IF NOT EXISTS idx_events_open ON events(is_open);

CREATE INDEX IF NOT EXISTS idx_mining_participation_event ON mining_participation(event_id);
CREATE INDEX IF NOT EXISTS idx_mining_participation_user ON mining_participation(member_id);
CREATE INDEX IF NOT EXISTS idx_mining_participation_channel ON mining_participation(channel_id);
CREATE INDEX IF NOT EXISTS idx_mining_participation_session ON mining_participation(session_start, session_end);
CREATE INDEX IF NOT EXISTS idx_mining_participation_org_member ON mining_participation(is_org_member);

CREATE INDEX IF NOT EXISTS idx_loans_guild_borrower ON loans(guild_id, borrower_id);
CREATE INDEX IF NOT EXISTS idx_loans_status ON loans(status);
CREATE INDEX IF NOT EXISTS idx_loans_due_date ON loans(due_date);

CREATE INDEX IF NOT EXISTS idx_materials_category ON materials(category);
CREATE INDEX IF NOT EXISTS idx_materials_name ON materials(name);

CREATE INDEX IF NOT EXISTS idx_mining_yields_participation ON mining_yields(participation_id);
CREATE INDEX IF NOT EXISTS idx_mining_yields_material ON mining_yields(material_id);

CREATE INDEX IF NOT EXISTS idx_command_usage_guild ON command_usage(guild_id);
CREATE INDEX IF NOT EXISTS idx_command_usage_user ON command_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_command_usage_command ON command_usage(command_name);
CREATE INDEX IF NOT EXISTS idx_command_usage_date ON command_usage(used_at);

CREATE INDEX IF NOT EXISTS idx_adhoc_sessions_creator ON adhoc_sessions(creator_id);
CREATE INDEX IF NOT EXISTS idx_adhoc_sessions_guild ON adhoc_sessions(guild_id);
CREATE INDEX IF NOT EXISTS idx_adhoc_sessions_status ON adhoc_sessions(status);

-- Insert some default materials
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
    ('Copper', 'ore', 1.5, 1.5)
ON CONFLICT (name) DO NOTHING;

-- Functions for common operations
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers to auto-update timestamps
DROP TRIGGER IF EXISTS trigger_users_updated_at ON users;
CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS trigger_guilds_updated_at ON guilds;
CREATE TRIGGER trigger_guilds_updated_at
    BEFORE UPDATE ON guilds
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS trigger_mining_channels_updated_at ON mining_channels;
CREATE TRIGGER trigger_mining_channels_updated_at
    BEFORE UPDATE ON mining_channels
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS trigger_mining_events_updated_at ON mining_events;
CREATE TRIGGER trigger_mining_events_updated_at
    BEFORE UPDATE ON mining_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS trigger_loans_updated_at ON loans;
CREATE TRIGGER trigger_loans_updated_at
    BEFORE UPDATE ON loans
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
