-- =====================================================
-- FIX EVENT ID CONSTRAINT FOR CURRENT FORMAT
-- Date: September 2025
-- Purpose: Ensure event ID constraint allows current sm-##### format
-- 
-- Issue: sm-60567 format failing constraint check
-- Solution: Update constraint to explicitly allow all working formats
-- =====================================================

BEGIN;

-- Drop any existing event ID format constraint
ALTER TABLE events DROP CONSTRAINT IF EXISTS check_event_id_format;

-- Add new constraint that explicitly allows current working formats
-- Format: 2-4 letter prefix + dash + 3-5 digits (flexible for various formats)
-- Examples: sm-123, sm-12345, op-67890, test-99999
ALTER TABLE events ADD CONSTRAINT check_event_id_format 
    CHECK (event_id ~ '^[a-z]{2,4}-[0-9]{3,5}$');

-- Record this migration as successful
INSERT INTO schema_migrations (migration_name, success, applied_at) 
VALUES ('13_fix_event_id_constraint.sql', TRUE, CURRENT_TIMESTAMP)
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================
-- 
-- Event ID format now supports:
-- - sm-123 (3 digits)
-- - sm-12345 (5 digits) 
-- - op-67890 (5 digits)
-- - All other valid combinations
-- =====================================================