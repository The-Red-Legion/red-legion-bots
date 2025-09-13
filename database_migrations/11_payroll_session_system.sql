-- Migration 11: Event-Driven Payroll Session System
-- Creates tables for managing stateful payroll calculation sessions

-- Payroll sessions for persistent state management
CREATE TABLE IF NOT EXISTS payroll_sessions (
    session_id TEXT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    event_id TEXT NOT NULL,
    event_type TEXT NOT NULL DEFAULT 'mining',
    current_step TEXT NOT NULL DEFAULT 'event_selected',
    ore_quantities JSONB DEFAULT '{}',
    pricing_data JSONB DEFAULT '{}',
    calculation_data JSONB DEFAULT '{}',
    donation_percentage INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '2 hours'),
    is_completed BOOLEAN DEFAULT FALSE
);

-- Index for efficient session lookups
CREATE INDEX IF NOT EXISTS idx_payroll_sessions_user_active 
    ON payroll_sessions(user_id, guild_id) 
    WHERE is_completed = FALSE;

CREATE INDEX IF NOT EXISTS idx_payroll_sessions_expires 
    ON payroll_sessions(expires_at) 
    WHERE is_completed = FALSE;

-- Session events log for debugging and analytics
CREATE TABLE IF NOT EXISTS payroll_session_events (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES payroll_sessions(session_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_data JSONB DEFAULT '{}',
    user_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for session event lookups
CREATE INDEX IF NOT EXISTS idx_payroll_session_events_session 
    ON payroll_session_events(session_id, created_at DESC);

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_payroll_session_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at on payroll_sessions
DROP TRIGGER IF EXISTS trigger_update_payroll_session_updated_at ON payroll_sessions;
CREATE TRIGGER trigger_update_payroll_session_updated_at
    BEFORE UPDATE ON payroll_sessions
    FOR EACH ROW EXECUTE FUNCTION update_payroll_session_updated_at();

-- Function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_payroll_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM payroll_sessions 
    WHERE expires_at < NOW() AND is_completed = FALSE;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ language 'plpgsql';

COMMENT ON TABLE payroll_sessions IS 'Persistent state management for payroll calculation workflows';
COMMENT ON TABLE payroll_session_events IS 'Event log for payroll session debugging and analytics';
COMMENT ON FUNCTION cleanup_expired_payroll_sessions() IS 'Removes expired payroll sessions to prevent database bloat';