-- Fix for missing events table
-- This script creates the events table that the /testdata command requires

-- Create events table if it doesn't exist
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    event_date DATE NOT NULL,
    event_time TIMESTAMP NOT NULL,
    event_name TEXT DEFAULT 'Sunday Mining',
    total_participants INTEGER DEFAULT 0,
    total_payout REAL,
    is_open BOOLEAN DEFAULT TRUE,
    payroll_calculated BOOLEAN DEFAULT FALSE,
    pdf_generated BOOLEAN DEFAULT FALSE,
    -- Legacy columns for backward compatibility
    event_id INTEGER GENERATED ALWAYS AS (id) STORED,
    channel_id TEXT,
    channel_name TEXT,
    start_time TEXT,
    end_time TEXT,
    total_value REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_events_guild_id ON events(guild_id);
CREATE INDEX IF NOT EXISTS idx_events_event_date ON events(event_date);
CREATE INDEX IF NOT EXISTS idx_events_is_open ON events(is_open);

-- Verify the table was created
SELECT 'events table created/verified successfully' as status;
