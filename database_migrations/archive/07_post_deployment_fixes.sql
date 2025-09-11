-- Migration: Post-Deployment Schema Fixes
-- Date: January 2025
-- Purpose: Apply manual fixes that were done on VM to prevent future deployment issues
-- This migration ensures schema consistency even if foundation migrations fail

BEGIN;

-- Step 1: Ensure guild_memberships has required columns
ALTER TABLE guild_memberships ADD COLUMN IF NOT EXISTS is_org_member BOOLEAN DEFAULT FALSE;

-- Step 2: Ensure events table has all required columns 
ALTER TABLE events ADD COLUMN IF NOT EXISTS name TEXT;
UPDATE events SET name = event_name WHERE name IS NULL;
ALTER TABLE events ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;

-- Step 3: Ensure mining_participation has proper foreign key to events table
DO $$
BEGIN
    -- Remove old foreign key if it exists
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'mining_participation_event_id_fkey' 
        AND table_name = 'mining_participation'
    ) THEN
        ALTER TABLE mining_participation DROP CONSTRAINT mining_participation_event_id_fkey;
    END IF;
    
    -- Add new foreign key constraint if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_mining_participation_events' 
        AND table_name = 'mining_participation'
    ) THEN
        ALTER TABLE mining_participation 
        ADD CONSTRAINT fk_mining_participation_events 
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE;
    END IF;
EXCEPTION
    WHEN others THEN
        RAISE NOTICE 'Could not modify foreign key constraints: %', SQLERRM;
END $$;

-- Step 4: Ensure guild exists and mining channels are configured
INSERT INTO guilds (guild_id, name, is_active) 
VALUES ('814699481912049704', 'Red Legion', true)
ON CONFLICT (guild_id) DO UPDATE SET
    name = EXCLUDED.name,
    is_active = EXCLUDED.is_active;

-- Clear existing mining channels and insert correct ones
DELETE FROM mining_channels WHERE guild_id = '814699481912049704';

INSERT INTO mining_channels (guild_id, channel_id, name, is_active) VALUES
    ('814699481912049704', '1385774416755163247', 'Dispatch/Main', true),
    ('814699481912049704', '1386367354753257583', 'Group Alpha', true),
    ('814699481912049704', '1385774498745159762', 'Group Bravo', true),
    ('814699481912049704', '1386344354930757782', 'Group Charlie', true),
    ('814699481912049704', '1386344411151204442', 'Group Delta', true),
    ('814699481912049704', '1386344461541445643', 'Group Echo', true),
    ('814699481912049704', '1386344513076854895', 'Group Foxtrot', true)
ON CONFLICT (channel_id) DO UPDATE SET
    name = EXCLUDED.name,
    is_active = EXCLUDED.is_active;

-- Step 5: Add helpful indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_events_name ON events(name);
CREATE INDEX IF NOT EXISTS idx_events_is_active ON events(is_active);
CREATE INDEX IF NOT EXISTS idx_mining_channels_guild_active ON mining_channels(guild_id, is_active);

-- Step 6: Add comments for documentation
COMMENT ON COLUMN events.name IS 'Alias for event_name - used by Sunday Mining code';
COMMENT ON COLUMN events.is_active IS 'Whether event is active - matches mining_events.status active';
COMMENT ON COLUMN guild_memberships.is_org_member IS 'Whether user is an organization member';
COMMENT ON TABLE mining_channels IS 'Voice channels configured for Sunday Mining operations';

COMMIT;

-- Verification queries (run these manually to verify migration success)
/*
-- Check events table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'events' AND column_name IN ('name', 'is_active', 'event_name');

-- Check guild_memberships table structure  
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'guild_memberships' AND column_name = 'is_org_member';

-- Check mining channels are configured
SELECT channel_id, name, is_active
FROM mining_channels 
WHERE guild_id = '814699481912049704' 
ORDER BY name;

-- Check foreign key constraints on mining_participation
SELECT constraint_name, table_name, column_name
FROM information_schema.key_column_usage 
WHERE table_name = 'mining_participation' AND constraint_name LIKE 'fk_%';
*/