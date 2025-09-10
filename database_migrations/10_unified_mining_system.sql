-- =====================================================
-- UNIFIED MINING SYSTEM MIGRATION
-- Date: January 2025  
-- Purpose: Complete database schema redesign for clean, unified mining system
-- 
-- BREAKING CHANGE: This migration drops all existing mining-related tables
-- and creates a clean, unified schema optimized for the Sunday Mining module
-- =====================================================

BEGIN;

-- =====================================================
-- CLEANUP: Remove Legacy Tables and Confusion
-- =====================================================

-- Drop all old mining-related tables to start fresh
DROP TABLE IF EXISTS mining_yields CASCADE;
DROP TABLE IF EXISTS mining_participation CASCADE;
DROP TABLE IF EXISTS mining_events CASCADE;
DROP TABLE IF EXISTS events CASCADE;
DROP TABLE IF EXISTS command_usage CASCADE;
DROP TABLE IF EXISTS adhoc_sessions CASCADE;

-- Drop related indexes that might exist
DROP INDEX IF EXISTS idx_mining_participation_event;
DROP INDEX IF EXISTS idx_mining_participation_user;
DROP INDEX IF EXISTS idx_mining_participation_channel;
DROP INDEX IF EXISTS idx_mining_participation_session;
DROP INDEX IF EXISTS idx_mining_participation_org_member;
DROP INDEX IF EXISTS idx_events_guild;
DROP INDEX IF EXISTS idx_events_date;
DROP INDEX IF EXISTS idx_events_open;
DROP INDEX IF EXISTS idx_mining_events_guild_date;
DROP INDEX IF EXISTS idx_mining_events_status;

-- Remove old migration tracking for clean slate
DROP TABLE IF EXISTS schema_migrations CASCADE;

-- =====================================================
-- FOUNDATION: Core Supporting Tables
-- =====================================================

-- Migration tracking table (recreated clean)
CREATE TABLE schema_migrations (
    migration_name VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    execution_time_ms INTEGER
);

-- Guilds table (if doesn't exist)
CREATE TABLE IF NOT EXISTS guilds (
    id BIGSERIAL PRIMARY KEY,
    guild_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    owner_id BIGINT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Users table (if doesn't exist)  
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username TEXT NOT NULL,
    display_name TEXT,
    is_active BOOLEAN DEFAULT true,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW()
);

-- Guild memberships (if doesn't exist)
CREATE TABLE IF NOT EXISTS guild_memberships (
    id BIGSERIAL PRIMARY KEY,
    guild_id TEXT REFERENCES guilds(guild_id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    is_org_member BOOLEAN DEFAULT false,
    member_rank TEXT,
    joined_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    UNIQUE(guild_id, user_id)
);

-- =====================================================
-- CORE UNIFIED MINING SYSTEM
-- =====================================================

-- Universal Events Table (THE central table)
CREATE TABLE events (
    -- Core Identity (THE most important fields)
    event_id TEXT PRIMARY KEY,                 -- 'sm-a7k2m9', 'op-b3x8n4', etc.
    guild_id BIGINT NOT NULL,                  -- Discord server
    event_type TEXT NOT NULL,                  -- 'mining', 'combat', 'salvage', 'social'
    event_name TEXT NOT NULL,                  -- "Sunday Mining", "Vanduul Raid"
    
    -- Leadership & Organization
    organizer_id BIGINT NOT NULL,              -- Who started/leads this event  
    organizer_name TEXT NOT NULL,              -- Display name for reports
    
    -- Time & Status Tracking
    started_at TIMESTAMP NOT NULL,             -- When tracking began
    ended_at TIMESTAMP,                        -- NULL = still active
    status TEXT NOT NULL CHECK (status IN ('open', 'closed')),
    
    -- Location Hierarchy (Stanton/Pyro system tracking)
    system_location TEXT,                      -- "Stanton", "Pyro", "Terra"
    planet_moon TEXT,                          -- "Daymar", "Lyria", "Magda"
    location_notes TEXT,                       -- "Shubin SAL-2", "Aaron Halo Belt A"
    
    -- Participation Metrics (Summary - details in participation table)
    total_participants INTEGER DEFAULT 0,
    max_concurrent INTEGER DEFAULT 0,
    total_duration_minutes INTEGER,
    
    -- Financial Tracking (Universal across event types)
    total_value_auec DECIMAL(15,2),           -- Ore value, bounties, etc.
    payroll_calculated BOOLEAN DEFAULT false,
    payroll_calculated_at TIMESTAMP,
    payroll_calculated_by_id BIGINT,
    
    -- Metadata & Context
    description TEXT,                          -- Optional event notes
    tags TEXT[],                              -- ['beginner-friendly', 'high-risk', 'training']
    
    -- System Fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Participation Tracking (Who did what, when, where)
CREATE TABLE participation (
    id SERIAL PRIMARY KEY,
    
    -- Event Link (THE key relationship)
    event_id TEXT REFERENCES events(event_id) ON DELETE CASCADE,
    
    -- Participant Identity
    user_id BIGINT NOT NULL,
    username TEXT NOT NULL,
    display_name TEXT,
    
    -- Channel/Location Tracking  
    channel_id BIGINT,                         -- Which voice channel
    channel_name TEXT,                         -- "Mining Alpha", "Combat Bravo"
    
    -- Time Tracking (Core for payroll)
    joined_at TIMESTAMP NOT NULL,
    left_at TIMESTAMP,                         -- NULL = still active
    duration_minutes INTEGER,                  -- Calculated on leave
    
    -- Member Status (Critical for lottery eligibility)
    is_org_member BOOLEAN DEFAULT false,
    member_rank TEXT,                          -- "Recruit", "Member", "Officer"
    org_join_date DATE,                        -- When they became org member
    
    -- Activity Metrics
    channel_switches INTEGER DEFAULT 0,        -- Channel movement tracking
    was_active BOOLEAN DEFAULT true,           -- Actual participation vs AFK
    
    -- System Fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- PAYROLL SYSTEM
-- =====================================================

-- Master Payroll Calculations
CREATE TABLE payrolls (
    id SERIAL PRIMARY KEY,
    payroll_id TEXT UNIQUE NOT NULL,           -- 'pay-sm-a7k2m9'
    event_id TEXT REFERENCES events(event_id) ON DELETE CASCADE,
    
    -- What Was Collected & Prices Used (Snapshot for auditing)
    total_scu_collected DECIMAL(10,2) NOT NULL,
    total_value_auec DECIMAL(15,2) NOT NULL,
    ore_prices_used JSONB NOT NULL,            -- Snapshot: {ore_name: {price, location, system}}
    mining_yields JSONB NOT NULL,             -- What was mined: {ore_name: scu_amount}
    
    -- Donation System Summary
    total_donated_auec DECIMAL(10,2) DEFAULT 0,
    
    -- Calculation Metadata
    calculated_by_id BIGINT NOT NULL,
    calculated_by_name TEXT NOT NULL,
    calculated_at TIMESTAMP DEFAULT NOW()
);

-- Individual Payouts (Final amounts after donations)
CREATE TABLE payouts (
    id SERIAL PRIMARY KEY,
    payroll_id TEXT REFERENCES payrolls(payroll_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    username TEXT NOT NULL,
    
    -- Payout Breakdown (Simple but complete)
    participation_minutes INTEGER NOT NULL,
    base_payout_auec DECIMAL(10,2) NOT NULL,     -- Before donations
    final_payout_auec DECIMAL(10,2) NOT NULL,    -- After donations (what they get)
    is_donor BOOLEAN DEFAULT false,              -- Did they donate earnings?
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- UEX CORP PRICING SYSTEM
-- =====================================================

-- Current UEX Corp Pricing (Minimal, Expandable)
CREATE TABLE uex_prices (
    id SERIAL PRIMARY KEY,
    
    -- Core Mining Data (What we need now)
    item_name TEXT NOT NULL,                    -- "Quantainium", "Bexalite"
    buy_price_per_scu DECIMAL(8,2) NOT NULL,   -- How much location pays buyers
    best_sell_location TEXT NOT NULL,           -- "Port Olisar", "Lorville"  
    system_location TEXT NOT NULL,              -- "Stanton", "Pyro"
    
    -- Category System (Future expansion ready)
    item_category TEXT NOT NULL DEFAULT 'ore',  -- 'ore', 'rmc', 'weapon', 'armor'
    
    -- API Tracking (12-hour refresh cycle)
    fetched_at TIMESTAMP DEFAULT NOW(),
    is_current BOOLEAN DEFAULT true
    
    -- Note: Unique current prices enforced via application logic
    -- CONSTRAINT unique_current_prices EXCLUDE (item_name WITH =, item_category WITH =) WHERE (is_current = true)
);

-- =====================================================
-- MEMBER ANALYTICS & REWARDS SYSTEM  
-- =====================================================

-- Member Statistics (Analytics for leaderboards and lottery)
CREATE TABLE member_stats (
    user_id BIGINT PRIMARY KEY,
    username TEXT NOT NULL,
    
    -- Monthly Counters (Reset each month)
    current_month_events INTEGER DEFAULT 0,
    current_month_minutes INTEGER DEFAULT 0,
    
    -- All-Time Counters
    total_events_all_time INTEGER DEFAULT 0,
    total_minutes_all_time INTEGER DEFAULT 0,
    
    -- Org Member Tracking (Critical for lottery eligibility)
    is_current_org_member BOOLEAN DEFAULT false,
    org_join_date DATE,
    monthly_events_as_org_member INTEGER DEFAULT 0,  -- Only org member events count
    total_org_events INTEGER DEFAULT 0,
    
    -- Streaks & Achievements
    current_streak_days INTEGER DEFAULT 0,
    longest_streak_days INTEGER DEFAULT 0,
    last_event_date DATE,
    
    -- Lottery System
    current_lottery_tickets INTEGER DEFAULT 0,   -- Based on monthly participation
    total_rewards_received DECIMAL(10,2) DEFAULT 0,
    
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Lottery Events (Org Member Rewards)
CREATE TABLE lottery_events (
    id SERIAL PRIMARY KEY,
    lottery_id TEXT UNIQUE NOT NULL,            -- 'lot-x7k2m9'
    guild_id BIGINT NOT NULL,
    title TEXT NOT NULL,                        -- "Monthly Mining Rewards"
    description TEXT,
    
    -- Prize Details
    total_prize_auec DECIMAL(15,2),
    prize_description TEXT,                     -- "1M aUEC + Prospector Ship"
    
    -- Eligibility Rules (Org-focused)
    org_members_only BOOLEAN DEFAULT true,      -- Main restriction
    min_events_required INTEGER DEFAULT 1,      -- Must attend X events
    min_org_tenure_days INTEGER DEFAULT 30,     -- Must be org member for X days
    eligible_event_types TEXT[],               -- ['mining', 'combat'] or NULL for all
    date_range_start DATE,
    date_range_end DATE,
    
    -- Lottery Status
    status TEXT CHECK (status IN ('open', 'closed', 'drawn')),
    drawing_date TIMESTAMP,
    winner_user_id BIGINT,
    winner_username TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Lottery Entries (Who entered with how many tickets)
CREATE TABLE lottery_entries (
    id SERIAL PRIMARY KEY,
    lottery_id TEXT REFERENCES lottery_events(lottery_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    username TEXT NOT NULL,
    ticket_count INTEGER NOT NULL,             -- More events = more tickets
    events_qualifying INTEGER NOT NULL,        -- Events that counted
    entered_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- PERFORMANCE INDEXES
-- =====================================================

-- Events table indexes
CREATE INDEX idx_events_guild_id ON events(guild_id);
CREATE INDEX idx_events_status ON events(status);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_organizer ON events(organizer_id);
CREATE INDEX idx_events_date ON events(started_at);
CREATE INDEX idx_events_location ON events(system_location, planet_moon);

-- Participation table indexes  
CREATE INDEX idx_participation_event ON participation(event_id);
CREATE INDEX idx_participation_user ON participation(user_id);
CREATE INDEX idx_participation_channel ON participation(channel_id);
CREATE INDEX idx_participation_time ON participation(joined_at, left_at);
CREATE INDEX idx_participation_org_member ON participation(is_org_member);
CREATE INDEX idx_participation_active ON participation(was_active);

-- Payroll system indexes
CREATE INDEX idx_payrolls_event ON payrolls(event_id);
CREATE INDEX idx_payrolls_calculated_by ON payrolls(calculated_by_id);
CREATE INDEX idx_payrolls_date ON payrolls(calculated_at);
CREATE INDEX idx_payouts_payroll ON payouts(payroll_id);
CREATE INDEX idx_payouts_user ON payouts(user_id);

-- UEX pricing indexes
CREATE INDEX idx_uex_prices_category ON uex_prices(item_category);
-- Partial index for current prices (compatible with older PostgreSQL)
CREATE INDEX idx_uex_prices_current ON uex_prices(is_current, item_name, item_category);
CREATE INDEX idx_uex_prices_fetched ON uex_prices(fetched_at);

-- Analytics & lottery indexes
CREATE INDEX idx_member_stats_org_member ON member_stats(is_current_org_member);
CREATE INDEX idx_member_stats_monthly ON member_stats(current_month_events);
CREATE INDEX idx_lottery_events_guild ON lottery_events(guild_id);
CREATE INDEX idx_lottery_events_status ON lottery_events(status);
CREATE INDEX idx_lottery_entries_lottery ON lottery_entries(lottery_id);
CREATE INDEX idx_lottery_entries_user ON lottery_entries(user_id);

-- =====================================================
-- DATA INTEGRITY CONSTRAINTS
-- =====================================================

-- Ensure event IDs follow prefixed format
ALTER TABLE events ADD CONSTRAINT check_event_id_format 
    CHECK (event_id ~ '^[a-z]{2,4}-[a-z0-9]{6}$');

-- Ensure participation time logic
ALTER TABLE participation ADD CONSTRAINT check_participation_time
    CHECK (left_at IS NULL OR left_at >= joined_at);

-- Ensure payroll amounts are positive
ALTER TABLE payouts ADD CONSTRAINT check_positive_payouts
    CHECK (base_payout_auec >= 0 AND final_payout_auec >= 0);

-- Ensure UEX prices are positive
ALTER TABLE uex_prices ADD CONSTRAINT check_positive_prices
    CHECK (buy_price_per_scu > 0);

-- =====================================================
-- HELPFUL COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON TABLE events IS 'Universal event tracking - THE central table that everything references';
COMMENT ON COLUMN events.event_id IS 'Prefixed unique identifier (sm-a7k2m9) - THE most important field';
COMMENT ON COLUMN events.status IS 'open = active/pending payroll, closed = payroll complete and archived';

COMMENT ON TABLE participation IS 'Individual participation tracking - who joined which event when';
COMMENT ON COLUMN participation.is_org_member IS 'Critical for lottery eligibility - must be org member';

COMMENT ON TABLE payrolls IS 'Master payroll calculations with price snapshots for auditing';
COMMENT ON COLUMN payrolls.ore_prices_used IS 'Frozen snapshot of prices used - enables audit trail';

COMMENT ON TABLE uex_prices IS 'Current UEX Corp pricing data - refreshes every 12 hours';
COMMENT ON COLUMN uex_prices.is_current IS 'Only one current price per item_name + item_category';

-- =====================================================
-- INITIAL DATA SETUP
-- =====================================================

-- Record this migration as successful
INSERT INTO schema_migrations (migration_name, success, applied_at) 
VALUES ('10_unified_mining_system.sql', TRUE, CURRENT_TIMESTAMP);

-- Add helpful initial data comment
INSERT INTO events (event_id, guild_id, event_type, event_name, organizer_id, organizer_name, started_at, status)
VALUES ('setup-000000', 0, 'system', 'Database Setup Complete', 0, 'System', NOW(), 'closed')
ON CONFLICT (event_id) DO NOTHING;

COMMIT;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================
-- 
-- This migration creates a clean, unified mining system optimized for:
-- 
-- ✅ Sunday Mining Operations (event tracking, payroll, donations)
-- ✅ UEX Corp Price Integration (12-hour refresh, snapshots)  
-- ✅ Member Analytics (participation tracking, leaderboards)
-- ✅ Lottery System (org member rewards based on participation)
-- ✅ Future Expansion (salvage, combat, other modules)
--
-- All tables use the event_id as the central linking key, making
-- cross-module queries simple and ensuring data integrity.
--
-- Schema is minimal but expandable - easy to add columns as new
-- modules reveal requirements without breaking existing functionality.
-- =====================================================