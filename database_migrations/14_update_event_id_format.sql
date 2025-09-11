-- =====================================================
-- UPDATE EVENT ID FORMAT TO NUMERIC SUFFIX
-- Date: January 2025
-- Purpose: Change event ID format from alphanumeric to 5-digit numeric suffix
-- 
-- Changes: sm-a7k2m9 → sm-12345, op-b3x8n4 → op-67890
-- =====================================================

BEGIN;

-- Drop the old constraint that expects 6 alphanumeric characters
ALTER TABLE events DROP CONSTRAINT IF EXISTS check_event_id_format;

-- Add new constraint that expects 5 numeric characters
-- Format: 2-4 letter prefix + dash + 5 digits
ALTER TABLE events ADD CONSTRAINT check_event_id_format 
    CHECK (event_id ~ '^[a-z]{2,4}-[0-9]{5}$');

-- Record this migration as successful
INSERT INTO schema_migrations (migration_name, success, applied_at) 
VALUES ('11_update_event_id_format.sql', TRUE, CURRENT_TIMESTAMP);

COMMIT;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================
-- 
-- Event IDs will now use format: prefix-12345
-- - More user-friendly (easier to read/type)
-- - No confusing characters (o/0, l/1)
-- - Shorter and cleaner for voice communication
-- - Existing events with old format will continue to work
-- =====================================================