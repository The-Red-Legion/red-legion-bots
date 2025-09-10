-- Migration: Fix Foundation Schema Conflicts
-- Date: January 2025
-- Purpose: Handle conflicts when foundation schema is applied to existing database
-- This migration runs BEFORE foundation schema to prepare the database

BEGIN;

-- Step 1: Drop conflicting indexes that reference columns that may not exist
DROP INDEX IF EXISTS idx_mining_participation_user;
DROP INDEX IF EXISTS idx_mining_participation_member;

-- Step 2: Add missing columns to existing tables if they don't exist
-- This prevents CREATE TABLE IF NOT EXISTS from failing when table exists but lacks columns

DO $$
BEGIN
    -- Add member_id to mining_participation if missing
    BEGIN
        ALTER TABLE mining_participation ADD COLUMN member_id VARCHAR(20);
    EXCEPTION 
        WHEN duplicate_column THEN
            RAISE NOTICE 'Column member_id already exists in mining_participation';
        WHEN undefined_table THEN
            RAISE NOTICE 'Table mining_participation does not exist yet - will be created by foundation schema';
    END;
    
    -- Add missing columns to events table if they exist but lack required columns
    BEGIN
        ALTER TABLE events ADD COLUMN IF NOT EXISTS event_name TEXT;
        ALTER TABLE events ADD COLUMN IF NOT EXISTS name TEXT;
        ALTER TABLE events ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
        ALTER TABLE events ADD COLUMN IF NOT EXISTS event_time TIMESTAMP;
        ALTER TABLE events ADD COLUMN IF NOT EXISTS total_value DECIMAL(15,2);
        ALTER TABLE events ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    EXCEPTION 
        WHEN undefined_table THEN
            RAISE NOTICE 'Table events does not exist yet - will be created by foundation schema';
    END;
    
    -- Ensure guild_id data type consistency
    BEGIN
        -- Check if events table exists and guild_id is VARCHAR, convert to BIGINT if needed
        IF EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'events' AND column_name = 'guild_id' AND data_type = 'character varying') THEN
            
            -- Create a backup column
            ALTER TABLE events ADD COLUMN guild_id_backup VARCHAR(20);
            UPDATE events SET guild_id_backup = guild_id;
            
            -- Drop and recreate with correct type
            ALTER TABLE events DROP COLUMN guild_id;
            ALTER TABLE events ADD COLUMN guild_id BIGINT;
            
            -- Convert and restore data
            UPDATE events SET guild_id = guild_id_backup::BIGINT WHERE guild_id_backup IS NOT NULL;
            ALTER TABLE events DROP COLUMN guild_id_backup;
            
            RAISE NOTICE 'Converted events.guild_id from VARCHAR to BIGINT';
        END IF;
    EXCEPTION 
        WHEN undefined_table THEN
            RAISE NOTICE 'Table events does not exist yet - will be created by foundation schema';
        WHEN OTHERS THEN
            RAISE NOTICE 'Could not convert guild_id data type: %', SQLERRM;
    END;
    
END $$;

-- Step 3: Create indexes safely
CREATE INDEX IF NOT EXISTS idx_mining_participation_user ON mining_participation(user_id) WHERE user_id IS NOT NULL;

-- Step 4: Add helpful comment
COMMENT ON TABLE mining_participation IS 'Foundation conflict fixes applied - ready for foundation schema';

COMMIT;

-- This migration ensures that foundation schema can be applied cleanly
-- regardless of the current database state