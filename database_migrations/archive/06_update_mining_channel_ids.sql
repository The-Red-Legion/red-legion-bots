-- Migration: Update Mining Channel IDs
-- Date: January 2025
-- Purpose: Update mining channel IDs to match current Discord server setup
-- Fixes: Incorrect channel IDs that were causing "Channel not found" errors

BEGIN;

-- Step 1: Update existing mining channels with correct IDs
-- This ensures database-stored channel configs match Discord reality

-- Clear any existing mining channels for the guild (they have wrong IDs)
-- Note: guild_id is VARCHAR, so use string literal
DELETE FROM mining_channels 
WHERE guild_id = '814699481912049704';

-- First ensure the guild exists
INSERT INTO guilds (guild_id, name, is_active) 
VALUES ('814699481912049704', 'Red Legion', true)
ON CONFLICT (guild_id) DO UPDATE SET
    name = EXCLUDED.name,
    is_active = EXCLUDED.is_active;

-- Insert correct mining channels with current Discord channel IDs
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

-- Step 2: Add helpful indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_mining_channels_guild_active 
ON mining_channels(guild_id, is_active);

-- Step 3: Add comments for documentation
COMMENT ON TABLE mining_channels IS 'Voice channels configured for Sunday Mining operations';

COMMIT;

-- Verification query (run manually to verify)
/*
SELECT 
    channel_id,
    name,
    is_active,
    created_at
FROM mining_channels 
WHERE guild_id = '814699481912049704' 
ORDER BY name;
*/