-- =====================================================
-- ALLOW TEST DATA PREFIX IN EVENT IDS
-- Date: September 2025
-- Purpose: Update event ID constraint to allow "ts-" prefix for test data
-- 
-- Changes: Add support for test data event IDs (ts-12345)
-- =====================================================

BEGIN;

-- Drop the old constraint
ALTER TABLE events DROP CONSTRAINT IF EXISTS check_event_id_format;

-- Add new constraint that allows both regular prefixes and test prefix
-- Format: 2-4 letter prefix + dash + 5 digits
-- Allows: sm-12345, op-67890, ts-12345, etc.
ALTER TABLE events ADD CONSTRAINT check_event_id_format 
    CHECK (event_id ~ '^[a-z]{2,4}-[0-9]{5}$');

-- Record this migration as successful
INSERT INTO schema_migrations (migration_name, success, applied_at) 
VALUES ('12_allow_test_prefix.sql', TRUE, CURRENT_TIMESTAMP);

COMMIT;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================
-- 
-- Test data event IDs with "ts-" prefix are now supported
-- Pattern allows any 2-4 character lowercase prefix including "ts"
-- =====================================================