"""
Database Schema Definitions

Contains all SQL schema definitions for the Red Legion Bot database.
"""

# Core schema - guilds and users
CORE_SCHEMA = """
-- Core guild management
CREATE TABLE IF NOT EXISTS guilds (
    id BIGINT PRIMARY KEY,                      -- Discord guild ID
    name TEXT NOT NULL,                         -- Guild name
    settings JSONB DEFAULT '{}',                -- Guild-specific settings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User management across guilds
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,                      -- Discord user ID
    username TEXT NOT NULL,                     -- Current username
    display_name TEXT,                          -- Display name
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Guild membership and roles
CREATE TABLE IF NOT EXISTS guild_memberships (
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    is_org_member BOOLEAN DEFAULT FALSE,
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (guild_id, user_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_guild_memberships_guild_id ON guild_memberships(guild_id);
CREATE INDEX IF NOT EXISTS idx_guild_memberships_user_id ON guild_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_guild_memberships_org_member ON guild_memberships(guild_id, is_org_member);
"""

# Mining schema - events, channels, participation
MINING_SCHEMA = """
-- Mining events
CREATE TABLE IF NOT EXISTS mining_events (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    event_date DATE NOT NULL,
    event_time TIMESTAMP NOT NULL,
    event_name TEXT DEFAULT 'Sunday Mining',
    status VARCHAR(20) DEFAULT 'planned' CHECK (status IN ('planned', 'active', 'completed', 'cancelled')),
    total_participants INTEGER DEFAULT 0,
    total_value_auec DECIMAL(15,2) DEFAULT 0,
    payroll_processed BOOLEAN DEFAULT FALSE,
    pdf_generated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mining channels (approved voice channels)
CREATE TABLE IF NOT EXISTS mining_channels (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    channel_id BIGINT NOT NULL,                 -- Discord voice channel ID
    channel_name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, channel_id)
);

-- Mining participation tracking
CREATE TABLE IF NOT EXISTS mining_participation (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES mining_events(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    channel_id BIGINT NOT NULL,
    session_start TIMESTAMP NOT NULL,
    session_end TIMESTAMP,
    duration_seconds INTEGER,
    is_org_member BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for mining operations
CREATE INDEX IF NOT EXISTS idx_mining_events_guild_date ON mining_events(guild_id, event_date);
CREATE INDEX IF NOT EXISTS idx_mining_events_status ON mining_events(guild_id, status);
CREATE INDEX IF NOT EXISTS idx_mining_channels_guild ON mining_channels(guild_id, is_active);
CREATE INDEX IF NOT EXISTS idx_mining_participation_event ON mining_participation(event_id);
CREATE INDEX IF NOT EXISTS idx_mining_participation_user ON mining_participation(user_id);
CREATE INDEX IF NOT EXISTS idx_mining_participation_session ON mining_participation(session_start, session_end);
"""

# Economy schema - materials, yields, loans
ECONOMY_SCHEMA = """
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

-- Loan system
CREATE TABLE IF NOT EXISTS loans (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT REFERENCES guilds(id) ON DELETE CASCADE,
    borrower_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    amount_auec DECIMAL(15,2) NOT NULL,
    interest_rate DECIMAL(5,4) DEFAULT 0.0000,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paid', 'defaulted')),
    issued_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP,
    paid_date TIMESTAMP
);

-- Indexes for economy operations
CREATE INDEX IF NOT EXISTS idx_materials_category ON materials(category);
CREATE INDEX IF NOT EXISTS idx_materials_name ON materials(name);
CREATE INDEX IF NOT EXISTS idx_mining_yields_participation ON mining_yields(participation_id);
CREATE INDEX IF NOT EXISTS idx_mining_yields_material ON mining_yields(material_id);
CREATE INDEX IF NOT EXISTS idx_loans_guild_borrower ON loans(guild_id, borrower_id);
CREATE INDEX IF NOT EXISTS idx_loans_status ON loans(guild_id, status);
"""

# Triggers for updated_at timestamps
TRIGGERS_SCHEMA = """
-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for auto-updating timestamps
DROP TRIGGER IF EXISTS update_guilds_updated_at ON guilds;
CREATE TRIGGER update_guilds_updated_at
    BEFORE UPDATE ON guilds
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_mining_events_updated_at ON mining_events;
CREATE TRIGGER update_mining_events_updated_at
    BEFORE UPDATE ON mining_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_materials_updated_at ON materials;
CREATE TRIGGER update_materials_updated_at
    BEFORE UPDATE ON materials
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
"""

# Complete schema in order
COMPLETE_SCHEMA = [
    CORE_SCHEMA,
    MINING_SCHEMA,
    ECONOMY_SCHEMA,
    TRIGGERS_SCHEMA,
]

# Schema metadata
SCHEMA_VERSION = "2.0.0"
SCHEMA_DESCRIPTION = "Red Legion Bot - Clean Database Architecture v2.0"
