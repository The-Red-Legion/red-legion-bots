-- =====================================================
-- COMPREHENSIVE DISCORD CHANNELS MANAGEMENT MIGRATION
-- Date: September 2025  
-- Purpose: Create comprehensive Discord channel tracking for all voice channels
-- =====================================================

BEGIN;

-- =====================================================
-- COMPREHENSIVE DISCORD CHANNELS TABLE
-- Track all Discord voice channels in the guild, not just mining
-- =====================================================

CREATE TABLE IF NOT EXISTS discord_channels (
    id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL UNIQUE,
    channel_name TEXT NOT NULL,
    channel_type TEXT NOT NULL DEFAULT 'voice' CHECK (channel_type IN ('voice', 'text', 'category')),
    
    -- Channel categorization
    category_id BIGINT,                    -- Discord category ID if in a category
    category_name TEXT,                    -- Category name for organization
    channel_purpose TEXT,                  -- mining, salvage, combat, general, social, etc.
    
    -- Channel status and metadata
    is_active BOOLEAN DEFAULT true,       -- Is this channel currently active/available
    is_trackable BOOLEAN DEFAULT true,    -- Should this channel be available for event tracking
    position INTEGER,                     -- Channel position in Discord
    
    -- Automatic sync tracking
    last_seen TIMESTAMP DEFAULT NOW(),    -- Last time this channel was seen in Discord
    first_discovered TIMESTAMP DEFAULT NOW(),
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_discord_channels_guild ON discord_channels(guild_id);
CREATE INDEX IF NOT EXISTS idx_discord_channels_active ON discord_channels(is_active, is_trackable);
CREATE INDEX IF NOT EXISTS idx_discord_channels_type ON discord_channels(channel_type);
CREATE INDEX IF NOT EXISTS idx_discord_channels_purpose ON discord_channels(channel_purpose);
CREATE INDEX IF NOT EXISTS idx_discord_channels_category ON discord_channels(category_id);
CREATE INDEX IF NOT EXISTS idx_discord_channels_last_seen ON discord_channels(last_seen);

-- =====================================================
-- MIGRATE DATA FROM MINING_CHANNELS TABLE
-- =====================================================

-- Insert existing mining channels into the new table
INSERT INTO discord_channels 
    (guild_id, channel_id, channel_name, channel_type, channel_purpose, is_active, is_trackable, created_at)
SELECT 
    guild_id::BIGINT,
    channel_id::BIGINT,
    name as channel_name,
    'voice' as channel_type,
    'mining' as channel_purpose,
    is_active,
    true as is_trackable,
    created_at
FROM mining_channels 
WHERE channel_id::BIGINT NOT IN (SELECT channel_id FROM discord_channels)
ON CONFLICT (channel_id) DO NOTHING;

-- =====================================================
-- CHANNEL SYNC FUNCTIONS
-- For keeping Discord channels up to date
-- =====================================================

-- Function to upsert channel data from Discord API sync
CREATE OR REPLACE FUNCTION upsert_discord_channel(
    p_guild_id BIGINT,
    p_channel_id BIGINT,
    p_channel_name TEXT,
    p_channel_type TEXT DEFAULT 'voice',
    p_category_id BIGINT DEFAULT NULL,
    p_category_name TEXT DEFAULT NULL,
    p_position INTEGER DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO discord_channels (
        guild_id, channel_id, channel_name, channel_type, 
        category_id, category_name, position, last_seen, updated_at
    )
    VALUES (
        p_guild_id, p_channel_id, p_channel_name, p_channel_type,
        p_category_id, p_category_name, p_position, NOW(), NOW()
    )
    ON CONFLICT (channel_id) 
    DO UPDATE SET
        channel_name = EXCLUDED.channel_name,
        channel_type = EXCLUDED.channel_type,
        category_id = EXCLUDED.category_id,
        category_name = EXCLUDED.category_name,
        position = EXCLUDED.position,
        last_seen = NOW(),
        updated_at = NOW(),
        is_active = true;  -- Mark as active when we see it
END;
$$ LANGUAGE plpgsql;

-- Function to mark channels as inactive that haven't been seen recently
CREATE OR REPLACE FUNCTION cleanup_inactive_channels(
    p_guild_id BIGINT,
    p_hours_threshold INTEGER DEFAULT 24
) RETURNS INTEGER AS $$
DECLARE
    affected_rows INTEGER;
BEGIN
    -- Mark channels as inactive if not seen in X hours
    UPDATE discord_channels 
    SET is_active = false, updated_at = NOW()
    WHERE guild_id = p_guild_id 
      AND last_seen < NOW() - (p_hours_threshold || ' hours')::INTERVAL
      AND is_active = true;
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    RETURN affected_rows;
END;
$$ LANGUAGE plpgsql;

-- Function to auto-categorize channels based on name patterns
CREATE OR REPLACE FUNCTION auto_categorize_channel(p_channel_id BIGINT) RETURNS TEXT AS $$
DECLARE
    current_channel_name TEXT;
    detected_purpose TEXT;
BEGIN
    SELECT channel_name INTO current_channel_name 
    FROM discord_channels 
    WHERE channel_id = p_channel_id;
    
    IF current_channel_name IS NULL THEN
        RETURN 'general';
    END IF;
    
    -- Auto-detect purpose based on channel name patterns
    current_channel_name := LOWER(current_channel_name);
    
    CASE 
        WHEN current_channel_name LIKE '%mining%' OR current_channel_name LIKE '%mine%' OR current_channel_name LIKE '%⛏%' THEN
            detected_purpose := 'mining';
        WHEN current_channel_name LIKE '%salvage%' OR current_channel_name LIKE '%salvaging%' OR current_channel_name LIKE '%🔧%' THEN
            detected_purpose := 'salvage';
        WHEN current_channel_name LIKE '%combat%' OR current_channel_name LIKE '%fight%' OR current_channel_name LIKE '%war%' OR current_channel_name LIKE '%⚔%' THEN
            detected_purpose := 'combat';
        WHEN current_channel_name LIKE '%explore%' OR current_channel_name LIKE '%exploration%' OR current_channel_name LIKE '%🚀%' THEN
            detected_purpose := 'exploration';
        WHEN current_channel_name LIKE '%trade%' OR current_channel_name LIKE '%trading%' OR current_channel_name LIKE '%market%' THEN
            detected_purpose := 'trading';
        WHEN current_channel_name LIKE '%social%' OR current_channel_name LIKE '%hangout%' OR current_channel_name LIKE '%chill%' THEN
            detected_purpose := 'social';
        WHEN current_channel_name LIKE '%general%' OR current_channel_name LIKE '%main%' OR current_channel_name LIKE '%lobby%' THEN
            detected_purpose := 'general';
        ELSE
            detected_purpose := 'general';
    END CASE;
    
    -- Update the channel with detected purpose
    UPDATE discord_channels 
    SET channel_purpose = detected_purpose, updated_at = NOW()
    WHERE channel_id = p_channel_id;
    
    RETURN detected_purpose;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- CHANNEL SYNC TRIGGER FOR AUTO-CATEGORIZATION
-- =====================================================

-- Trigger to auto-categorize channels when inserted/updated
CREATE OR REPLACE FUNCTION trigger_auto_categorize_channel()
RETURNS TRIGGER AS $$
BEGIN
    -- Only auto-categorize if no purpose is set or if it's 'general'
    IF NEW.channel_purpose IS NULL OR NEW.channel_purpose = 'general' THEN
        NEW.channel_purpose := auto_categorize_channel(NEW.channel_id);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auto_categorize_discord_channels
    BEFORE INSERT OR UPDATE ON discord_channels
    FOR EACH ROW
    EXECUTE FUNCTION trigger_auto_categorize_channel();

-- =====================================================
-- VIEWS FOR EASY QUERYING
-- =====================================================

-- View for active trackable channels
CREATE OR REPLACE VIEW active_voice_channels AS
SELECT 
    channel_id,
    channel_name,
    channel_purpose,
    category_name,
    position,
    guild_id,
    last_seen
FROM discord_channels 
WHERE is_active = true 
  AND is_trackable = true 
  AND channel_type = 'voice'
ORDER BY 
    CASE channel_purpose 
        WHEN 'mining' THEN 1
        WHEN 'salvage' THEN 2 
        WHEN 'combat' THEN 3
        WHEN 'exploration' THEN 4
        WHEN 'trading' THEN 5
        WHEN 'social' THEN 6
        ELSE 7
    END,
    channel_name;

-- View for channel statistics
CREATE OR REPLACE VIEW discord_channel_stats AS
SELECT 
    guild_id,
    channel_type,
    channel_purpose,
    COUNT(*) as total_channels,
    COUNT(CASE WHEN is_active THEN 1 END) as active_channels,
    COUNT(CASE WHEN is_trackable THEN 1 END) as trackable_channels,
    MAX(last_seen) as most_recent_sync
FROM discord_channels
GROUP BY guild_id, channel_type, channel_purpose;

-- =====================================================
-- SAMPLE DATA AND TESTING
-- =====================================================

-- Add some sample channels to test the system (using high channel IDs to avoid conflicts)
INSERT INTO discord_channels 
    (guild_id, channel_id, channel_name, channel_type, channel_purpose, category_name)
VALUES 
    (814699481912049704, 999999999999999999, '🎤 General Voice', 'voice', 'general', 'General'),
    (814699481912049704, 999999999999999998, '🚀 Exploration Alpha', 'voice', 'exploration', 'Operations'),
    (814699481912049704, 999999999999999997, '⚔️ Combat Operations', 'voice', 'combat', 'Operations'),
    (814699481912049704, 999999999999999996, '🏪 Trading Hub', 'voice', 'trading', 'Commerce'),
    (814699481912049704, 999999999999999995, '🍺 Social Lounge', 'voice', 'social', 'Community')
ON CONFLICT (channel_id) DO NOTHING;

-- =====================================================
-- MIGRATION COMPLETION
-- =====================================================

-- Insert migration record
INSERT INTO schema_migrations (migration_name, applied_at, success) 
VALUES ('18_comprehensive_discord_channels', NOW(), true)
ON CONFLICT (migration_name) DO UPDATE SET
    applied_at = NOW(),
    success = true;

COMMIT;

-- =====================================================
-- VERIFICATION QUERIES (For testing)
-- =====================================================

-- Verify new table exists and has data
SELECT 
    'Total channels' as metric,
    COUNT(*) as count 
FROM discord_channels
UNION ALL
SELECT 
    'Active channels' as metric,
    COUNT(*) as count 
FROM discord_channels 
WHERE is_active = true;

-- Show channel breakdown by purpose
SELECT 
    channel_purpose,
    COUNT(*) as channel_count,
    string_agg(channel_name, ', ' ORDER BY channel_name) as channels
FROM discord_channels 
WHERE is_active = true
GROUP BY channel_purpose
ORDER BY channel_count DESC;

-- Test auto-categorization function
SELECT 
    channel_name,
    channel_purpose,
    auto_categorize_channel(channel_id) as detected_purpose
FROM discord_channels 
LIMIT 5;