-- =====================================================
-- EVENT SCHEDULING AND REAL-TIME MONITORING MIGRATION
-- Date: September 2025  
-- Purpose: Add event scheduling capabilities and real-time monitoring support
-- =====================================================

BEGIN;

-- =====================================================
-- EVENTS TABLE ENHANCEMENTS
-- Add scheduling and tracking fields
-- =====================================================

ALTER TABLE events ADD COLUMN IF NOT EXISTS scheduled_start_time TIMESTAMP;
ALTER TABLE events ADD COLUMN IF NOT EXISTS auto_start_enabled BOOLEAN DEFAULT false;
ALTER TABLE events ADD COLUMN IF NOT EXISTS tracked_channels JSONB;
ALTER TABLE events ADD COLUMN IF NOT EXISTS primary_channel_id BIGINT;
ALTER TABLE events ADD COLUMN IF NOT EXISTS event_status TEXT DEFAULT 'planned' CHECK (event_status IN ('planned', 'scheduled', 'live', 'completed', 'cancelled'));

-- Update existing events to have proper event_status
UPDATE events SET event_status = CASE 
    WHEN status = 'open' AND ended_at IS NULL THEN 'live'
    WHEN status = 'closed' AND ended_at IS NOT NULL THEN 'completed'
    ELSE 'completed'
END WHERE event_status = 'planned';

-- Add indexes for better performance on new fields
CREATE INDEX IF NOT EXISTS idx_events_scheduled_start ON events(scheduled_start_time);
CREATE INDEX IF NOT EXISTS idx_events_auto_start ON events(auto_start_enabled);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(event_status);
CREATE INDEX IF NOT EXISTS idx_events_primary_channel ON events(primary_channel_id);

-- =====================================================
-- REAL-TIME PARTICIPATION TRACKING
-- Enhanced participation tracking for live monitoring
-- =====================================================

-- Add real-time fields to participation table
ALTER TABLE participation ADD COLUMN IF NOT EXISTS is_currently_active BOOLEAN DEFAULT false;
ALTER TABLE participation ADD COLUMN IF NOT EXISTS session_duration_seconds INTEGER DEFAULT 0;
ALTER TABLE participation ADD COLUMN IF NOT EXISTS last_activity_update TIMESTAMP DEFAULT NOW();

-- Create index for real-time queries
CREATE INDEX IF NOT EXISTS idx_participation_active ON participation(event_id, is_currently_active);
CREATE INDEX IF NOT EXISTS idx_participation_last_activity ON participation(last_activity_update);

-- =====================================================
-- EVENT PARTICIPANT SNAPSHOTS
-- Table for storing real-time participant count snapshots for graphing
-- =====================================================

CREATE TABLE IF NOT EXISTS event_participant_snapshots (
    id SERIAL PRIMARY KEY,
    event_id TEXT REFERENCES events(event_id) ON DELETE CASCADE,
    snapshot_time TIMESTAMP NOT NULL DEFAULT NOW(),
    total_participants INTEGER NOT NULL DEFAULT 0,
    active_participants INTEGER NOT NULL DEFAULT 0,
    channel_breakdown JSONB, -- {"channel_123": 5, "channel_456": 3}
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for efficient time-series queries
CREATE INDEX IF NOT EXISTS idx_snapshots_event_time ON event_participant_snapshots(event_id, snapshot_time);
CREATE INDEX IF NOT EXISTS idx_snapshots_time ON event_participant_snapshots(snapshot_time);

-- =====================================================
-- SCHEDULED EVENTS QUEUE
-- Table for tracking scheduled events and their execution status  
-- =====================================================

CREATE TABLE IF NOT EXISTS scheduled_event_queue (
    id SERIAL PRIMARY KEY,
    event_id TEXT REFERENCES events(event_id) ON DELETE CASCADE,
    scheduled_for TIMESTAMP NOT NULL,
    execution_status TEXT DEFAULT 'pending' CHECK (execution_status IN ('pending', 'executing', 'completed', 'failed', 'cancelled')),
    execution_started_at TIMESTAMP,
    execution_completed_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for scheduler queries
CREATE INDEX IF NOT EXISTS idx_queue_scheduled_for ON scheduled_event_queue(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_queue_status ON scheduled_event_queue(execution_status);
CREATE INDEX IF NOT EXISTS idx_queue_event_id ON scheduled_event_queue(event_id);

-- =====================================================
-- EVENT METRICS SUMMARY
-- Table for storing computed real-time metrics
-- =====================================================

CREATE TABLE IF NOT EXISTS event_metrics (
    id SERIAL PRIMARY KEY,
    event_id TEXT REFERENCES events(event_id) ON DELETE CASCADE,
    metric_time TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Participant metrics
    current_participant_count INTEGER DEFAULT 0,
    peak_participant_count INTEGER DEFAULT 0,
    total_unique_participants INTEGER DEFAULT 0,
    
    -- Duration metrics  
    event_duration_minutes INTEGER DEFAULT 0,
    average_session_duration_minutes DECIMAL(10,2) DEFAULT 0,
    
    -- Channel breakdown
    channel_metrics JSONB, -- {"channel_123": {"name": "Mining Alpha", "count": 5, "duration": 120}}
    
    -- Update tracking
    last_updated TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(event_id, metric_time)
);

-- Index for real-time metric queries
CREATE INDEX IF NOT EXISTS idx_metrics_event_time ON event_metrics(event_id, metric_time);
CREATE INDEX IF NOT EXISTS idx_metrics_last_updated ON event_metrics(last_updated);

-- =====================================================
-- FUNCTIONS FOR REAL-TIME UPDATES
-- =====================================================

-- Function to update participation session duration
CREATE OR REPLACE FUNCTION update_participation_duration(
    p_event_id TEXT,
    p_user_id BIGINT,
    p_channel_id BIGINT
) RETURNS VOID AS $$
DECLARE
    session_start TIMESTAMP;
    duration_seconds INTEGER;
BEGIN
    -- Find the most recent active session for this user
    SELECT joined_at INTO session_start
    FROM participation 
    WHERE event_id = p_event_id 
      AND user_id = p_user_id 
      AND channel_id = p_channel_id
      AND is_currently_active = true
    ORDER BY joined_at DESC
    LIMIT 1;
    
    IF session_start IS NOT NULL THEN
        -- Calculate duration in seconds
        duration_seconds := EXTRACT(EPOCH FROM (NOW() - session_start));
        
        -- Update the session duration
        UPDATE participation 
        SET session_duration_seconds = duration_seconds,
            last_activity_update = NOW()
        WHERE event_id = p_event_id 
          AND user_id = p_user_id 
          AND channel_id = p_channel_id
          AND joined_at = session_start;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to create participant snapshot
CREATE OR REPLACE FUNCTION create_participant_snapshot(p_event_id TEXT) RETURNS VOID AS $$
DECLARE
    total_count INTEGER;
    active_count INTEGER;
    channel_data JSONB;
BEGIN
    -- Count total and active participants
    SELECT 
        COUNT(DISTINCT user_id),
        COUNT(DISTINCT CASE WHEN is_currently_active THEN user_id END)
    INTO total_count, active_count
    FROM participation 
    WHERE event_id = p_event_id;
    
    -- Get channel breakdown
    SELECT jsonb_object_agg(channel_id::text, channel_count)
    INTO channel_data
    FROM (
        SELECT channel_id, COUNT(DISTINCT user_id) as channel_count
        FROM participation 
        WHERE event_id = p_event_id 
          AND is_currently_active = true
        GROUP BY channel_id
    ) channel_stats;
    
    -- Insert snapshot
    INSERT INTO event_participant_snapshots 
    (event_id, total_participants, active_participants, channel_breakdown)
    VALUES (p_event_id, total_count, active_count, COALESCE(channel_data, '{}'::jsonb));
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- MIGRATION COMPLETION
-- =====================================================

-- Insert migration record
INSERT INTO schema_migrations (migration_name, applied_at, success) 
VALUES ('17_event_scheduling_and_monitoring', NOW(), true)
ON CONFLICT (migration_name) DO UPDATE SET
    applied_at = NOW(),
    success = true;

COMMIT;

-- =====================================================
-- VERIFICATION QUERIES (For testing)
-- =====================================================

-- Verify new columns exist
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'events' 
  AND column_name IN ('scheduled_start_time', 'auto_start_enabled', 'tracked_channels', 'primary_channel_id', 'event_status');

-- Verify new tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_name IN ('event_participant_snapshots', 'scheduled_event_queue', 'event_metrics');

-- Verify functions exist  
SELECT routine_name 
FROM information_schema.routines 
WHERE routine_name IN ('update_participation_duration', 'create_participant_snapshot');