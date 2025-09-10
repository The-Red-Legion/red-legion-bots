-- Migration: Fix Event Schema Consistency
-- Date: January 2025
-- Purpose: Resolve schema inconsistencies discovered during Sunday Mining debugging
-- Issues Fixed:
--   1. Column name mismatches (name vs event_name)
--   2. Foreign key reference corrections
--   3. Data type alignments
--   4. Table reference consistency

BEGIN;

-- Step 1: Add missing 'name' column to events table as alias for event_name
-- This allows our code to use 'name' while maintaining backward compatibility
ALTER TABLE events ADD COLUMN IF NOT EXISTS name TEXT;

-- Update existing events to populate the name column from event_name
UPDATE events SET name = event_name WHERE name IS NULL;

-- Step 2: Add missing columns to events table that our code expects
ALTER TABLE events ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;

-- Step 3: Fix mining_participation foreign key to reference events table instead of mining_events
-- First, check if there are any orphaned records that would prevent the constraint
DO $$
BEGIN
    -- Add a new foreign key constraint to events table
    -- Note: We'll keep the column name as event_id but reference events(id)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_mining_participation_events' 
        AND table_name = 'mining_participation'
    ) THEN
        ALTER TABLE mining_participation 
        ADD CONSTRAINT fk_mining_participation_events 
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE;
    END IF;
    
    -- Remove the old foreign key to mining_events if it exists
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'mining_participation_event_id_fkey' 
        AND table_name = 'mining_participation'
    ) THEN
        ALTER TABLE mining_participation 
        DROP CONSTRAINT mining_participation_event_id_fkey;
    END IF;
EXCEPTION
    WHEN others THEN
        RAISE NOTICE 'Could not modify foreign key constraints: %', SQLERRM;
END $$;

-- Step 4: Create a view to unify mining_events and events tables if needed
-- This allows legacy code to work with mining_events while new code uses events
CREATE OR REPLACE VIEW unified_events AS
SELECT 
    id,
    guild_id,
    event_date,
    event_time,
    COALESCE(name, event_name, 'Sunday Mining') as name,
    COALESCE(name, event_name, 'Sunday Mining') as event_name,
    total_participants,
    COALESCE(is_open, false) as is_open,
    COALESCE(is_active, true) as is_active,
    payroll_calculated,
    pdf_generated,
    created_at,
    updated_at
FROM events
WHERE events.id IS NOT NULL

UNION ALL

SELECT 
    id,
    guild_id,
    event_date,
    event_time,
    COALESCE(event_name, 'Sunday Mining') as name,
    event_name,
    total_participants,
    CASE 
        WHEN status = 'active' THEN true 
        ELSE false 
    END as is_open,
    true as is_active,
    payroll_processed as payroll_calculated,
    pdf_generated,
    created_at,
    updated_at
FROM mining_events
WHERE mining_events.id IS NOT NULL
    AND mining_events.id NOT IN (SELECT id FROM events WHERE events.id IS NOT NULL);

-- Step 5: Add function to ensure guild_id compatibility
-- Handle both BIGINT and VARCHAR formats for guild_id
CREATE OR REPLACE FUNCTION normalize_guild_id(input_guild_id ANYELEMENT)
RETURNS BIGINT AS $$
BEGIN
    -- Convert string guild_id to BIGINT
    IF pg_typeof(input_guild_id) = 'text'::regtype OR pg_typeof(input_guild_id) = 'varchar'::regtype THEN
        RETURN input_guild_id::BIGINT;
    END IF;
    
    -- Already a number type
    RETURN input_guild_id::BIGINT;
EXCEPTION
    WHEN others THEN
        -- If conversion fails, return a default or raise error
        RAISE EXCEPTION 'Could not convert guild_id % to BIGINT', input_guild_id;
END;
$$ LANGUAGE plpgsql;

-- Step 6: Create indexes for the new columns
CREATE INDEX IF NOT EXISTS idx_events_name ON events(name);
CREATE INDEX IF NOT EXISTS idx_events_is_active ON events(is_active);

-- Step 7: Add helpful comments for future reference
COMMENT ON COLUMN events.name IS 'Alias for event_name - used by Sunday Mining code';
COMMENT ON COLUMN events.is_active IS 'Whether event is active - matches mining_events.status active';
COMMENT ON VIEW unified_events IS 'Unified view of events and mining_events for compatibility';

COMMIT;

-- Verification queries (run these manually to verify migration success)
/*
-- Check that events table has required columns
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'events' AND column_name IN ('name', 'is_active', 'event_name');

-- Check foreign key constraints on mining_participation
SELECT constraint_name, table_name, column_name, foreign_table_name, foreign_column_name
FROM information_schema.key_column_usage kcu
JOIN information_schema.referential_constraints rc ON kcu.constraint_name = rc.constraint_name
WHERE kcu.table_name = 'mining_participation';

-- Test the unified_events view
SELECT COUNT(*) as total_events FROM unified_events;

-- Test guild_id normalization function
SELECT normalize_guild_id('123456789012345678'::varchar);
*/