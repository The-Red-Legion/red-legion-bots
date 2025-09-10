-- Database Migration: Add Prefixed Event ID Support
-- Date: 2025-09-09
-- Purpose: Modify event_id column to support prefixed string IDs (e.g., 'sm-a7k2m9')

-- =====================================================
-- BACKUP RECOMMENDATION
-- =====================================================
-- IMPORTANT: Run this backup command before executing migration:
-- pg_dump -h your-host -U your-user -d your-database -t mining_events > mining_events_backup.sql

-- =====================================================
-- MIGRATION SCRIPT
-- =====================================================

BEGIN;

-- Check current schema of event_id column
SELECT 
    column_name, 
    data_type, 
    character_maximum_length, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'mining_events' AND column_name = 'event_id';

-- Step 1: Add a temporary column for prefixed event IDs
-- (This approach preserves existing data and allows rollback)
ALTER TABLE mining_events 
ADD COLUMN event_id_prefixed VARCHAR(50);

-- Step 2: Create unique index on the new prefixed column
CREATE UNIQUE INDEX idx_mining_events_prefixed_id ON mining_events(event_id_prefixed);

-- Step 3: Generate prefixed IDs for existing records
-- This will create IDs like 'sm-000001', 'sm-000002', etc. for existing events
UPDATE mining_events 
SET event_id_prefixed = 'sm-' || LPAD(event_id::text, 6, '0')
WHERE event_id_prefixed IS NULL 
  AND event_type = 'mining';

-- For non-mining events, use appropriate prefixes
UPDATE mining_events 
SET event_id_prefixed = 
  CASE 
    WHEN event_type = 'operation' THEN 'op-' || LPAD(event_id::text, 6, '0')
    WHEN event_type = 'training' THEN 'tr-' || LPAD(event_id::text, 6, '0')
    WHEN event_type = 'social' THEN 'sc-' || LPAD(event_id::text, 6, '0')
    WHEN event_type = 'tournament' THEN 'tm-' || LPAD(event_id::text, 6, '0')
    WHEN event_type = 'expedition' THEN 'ex-' || LPAD(event_id::text, 6, '0')
    ELSE 'ev-' || LPAD(event_id::text, 6, '0')
  END
WHERE event_id_prefixed IS NULL;

-- Step 4: Verify all records have prefixed IDs
SELECT COUNT(*) as records_without_prefixed_id 
FROM mining_events 
WHERE event_id_prefixed IS NULL;

-- Step 5: Update related tables to use prefixed event IDs
-- (Note: This step depends on your foreign key relationships)

-- Update mining_participation table if it references event_id
-- ALTER TABLE mining_participation ADD COLUMN event_id_prefixed VARCHAR(50);
-- UPDATE mining_participation SET event_id_prefixed = (
--     SELECT event_id_prefixed 
--     FROM mining_events 
--     WHERE mining_events.event_id = mining_participation.event_id
-- );

-- Step 6: Rename columns to switch to prefixed system
-- (Uncomment these lines after verifying the migration works)
-- ALTER TABLE mining_events RENAME COLUMN event_id TO event_id_old;
-- ALTER TABLE mining_events RENAME COLUMN event_id_prefixed TO event_id;

-- Step 7: Drop old column (ONLY after confirming everything works)
-- ALTER TABLE mining_events DROP COLUMN event_id_old;

-- Add constraints
ALTER TABLE mining_events 
ALTER COLUMN event_id_prefixed SET NOT NULL;

-- Create function to validate event ID format
CREATE OR REPLACE FUNCTION validate_event_id_format(event_id TEXT) 
RETURNS BOOLEAN AS $$
BEGIN
    -- Check format: prefix-suffix where prefix is 2-4 chars, suffix is 4-10 alphanumeric
    RETURN event_id ~ '^[a-z]{2,4}-[a-z0-9]{4,10}$';
END;
$$ LANGUAGE plpgsql;

-- Add check constraint for event ID format
ALTER TABLE mining_events 
ADD CONSTRAINT chk_event_id_format 
CHECK (validate_event_id_format(event_id_prefixed));

-- Step 8: Create indexes for performance
CREATE INDEX idx_mining_events_event_type ON mining_events(event_type);
CREATE INDEX idx_mining_events_status ON mining_events(status);
CREATE INDEX idx_mining_events_guild_date ON mining_events(guild_id, event_date);

-- Display summary
SELECT 
    event_type,
    COUNT(*) as event_count,
    MIN(event_id_prefixed) as sample_prefixed_id
FROM mining_events 
GROUP BY event_type
ORDER BY event_count DESC;

COMMIT;

-- =====================================================
-- ROLLBACK SCRIPT (if needed)
-- =====================================================
-- If you need to rollback this migration:
/*
BEGIN;
ALTER TABLE mining_events DROP CONSTRAINT IF EXISTS chk_event_id_format;
DROP FUNCTION IF EXISTS validate_event_id_format;
DROP INDEX IF EXISTS idx_mining_events_prefixed_id;
ALTER TABLE mining_events DROP COLUMN IF EXISTS event_id_prefixed;
COMMIT;
*/

-- =====================================================
-- POST-MIGRATION VERIFICATION
-- =====================================================
-- Run these queries to verify the migration:
-- 1. Check all events have valid prefixed IDs:
--    SELECT event_id_prefixed FROM mining_events WHERE NOT validate_event_id_format(event_id_prefixed);
--
-- 2. Verify event type distribution:
--    SELECT event_type, COUNT(*), array_agg(event_id_prefixed ORDER BY created_at LIMIT 3) as sample_ids
--    FROM mining_events GROUP BY event_type;
--
-- 3. Test event creation with new format:
--    INSERT INTO mining_events (event_id_prefixed, guild_id, name, event_date, event_type, status, is_active)
--    VALUES ('sm-test01', '123456789', 'Test Event', CURRENT_DATE, 'mining', 'active', true);