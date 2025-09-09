-- Migration: Add Missing Tables for Slash Command System
-- Date: 2025-09-08
-- Purpose: Add required database tables for the new slash command functionality

-- Market items table for red-market commands
CREATE TABLE IF NOT EXISTS market_items (
    item_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(15,2) NOT NULL CHECK (price > 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    category VARCHAR(50) DEFAULT 'general',
    seller_id VARCHAR(20),
    seller_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bot configuration table for red-config commands
CREATE TABLE IF NOT EXISTS bot_config (
    config_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    config_key VARCHAR(100) NOT NULL,
    config_value TEXT,
    config_type VARCHAR(20) DEFAULT 'string', -- string, integer, boolean, json
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, config_key)
);

-- Command usage tracking for analytics
CREATE TABLE IF NOT EXISTS command_usage (
    usage_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    user_id VARCHAR(20) REFERENCES users(user_id),
    command_name VARCHAR(100) NOT NULL,
    command_type VARCHAR(20) DEFAULT 'slash', -- slash, prefix, context
    success BOOLEAN DEFAULT TRUE,
    execution_time_ms INTEGER,
    error_message TEXT,
    parameters JSON,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Admin actions log for red-admin commands
CREATE TABLE IF NOT EXISTS admin_actions (
    action_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    admin_id VARCHAR(20) REFERENCES users(user_id),
    admin_name VARCHAR(100),
    action_type VARCHAR(50) NOT NULL, -- restart, config_refresh, add_channel, remove_channel
    target_resource VARCHAR(100), -- channel_id, config_key, etc.
    action_details JSON,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_market_items_guild ON market_items(guild_id);
CREATE INDEX IF NOT EXISTS idx_market_items_active ON market_items(is_active);
CREATE INDEX IF NOT EXISTS idx_market_items_category ON market_items(category);
CREATE INDEX IF NOT EXISTS idx_market_items_price ON market_items(price);

CREATE INDEX IF NOT EXISTS idx_bot_config_guild_key ON bot_config(guild_id, config_key);
CREATE INDEX IF NOT EXISTS idx_bot_config_active ON bot_config(is_active);

CREATE INDEX IF NOT EXISTS idx_command_usage_guild ON command_usage(guild_id);
CREATE INDEX IF NOT EXISTS idx_command_usage_user ON command_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_command_usage_command ON command_usage(command_name);
CREATE INDEX IF NOT EXISTS idx_command_usage_used_at ON command_usage(used_at);

CREATE INDEX IF NOT EXISTS idx_admin_actions_guild ON admin_actions(guild_id);
CREATE INDEX IF NOT EXISTS idx_admin_actions_admin ON admin_actions(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_actions_type ON admin_actions(action_type);
CREATE INDEX IF NOT EXISTS idx_admin_actions_performed_at ON admin_actions(performed_at);

-- Insert default market categories
INSERT INTO market_items (guild_id, name, description, price, stock, category, seller_name, is_active) 
VALUES 
    (NULL, 'Example Mining Tool', 'High-quality mining laser for efficient resource extraction', 50000, 10, 'mining_equipment', 'Red Legion Supply', false),
    (NULL, 'Combat Armor Set', 'Military-grade armor for dangerous operations', 75000, 5, 'combat_gear', 'Red Legion Armory', false),
    (NULL, 'Ship Component - Power Plant', 'Upgraded power plant for enhanced ship performance', 120000, 3, 'ship_components', 'Red Legion Engineering', false)
ON CONFLICT DO NOTHING;

-- Insert default bot configuration keys
INSERT INTO bot_config (guild_id, config_key, config_value, config_type, description) 
VALUES 
    (NULL, 'mining_session_duration_hours', '4', 'integer', 'Default duration for mining sessions in hours'),
    (NULL, 'payroll_calculation_enabled', 'true', 'boolean', 'Enable automatic payroll calculations'),
    (NULL, 'event_auto_cleanup_days', '30', 'integer', 'Days after which completed events are archived'),
    (NULL, 'max_loan_amount', '1000000', 'integer', 'Maximum loan amount in credits'),
    (NULL, 'loan_interest_rate', '0.05', 'string', 'Default interest rate for organization loans'),
    (NULL, 'market_commission_rate', '0.02', 'string', 'Commission rate for market transactions')
ON CONFLICT (guild_id, config_key) DO NOTHING;

-- Add constraints for data validation
ALTER TABLE market_items 
ADD CONSTRAINT chk_market_category 
CHECK (category IN ('general', 'mining_equipment', 'combat_gear', 'ship_components', 'consumables', 'blueprints'));

ALTER TABLE bot_config 
ADD CONSTRAINT chk_config_type 
CHECK (config_type IN ('string', 'integer', 'boolean', 'json'));

ALTER TABLE command_usage 
ADD CONSTRAINT chk_command_type 
CHECK (command_type IN ('slash', 'prefix', 'context', 'button', 'modal'));

ALTER TABLE admin_actions 
ADD CONSTRAINT chk_action_type 
CHECK (action_type IN ('restart', 'config_refresh', 'add_channel', 'remove_channel', 'update_config', 'sync_commands', 'emergency_stop'));

-- Create view for active market items with seller info
CREATE OR REPLACE VIEW active_market_items AS
SELECT 
    mi.item_id,
    mi.guild_id,
    mi.name,
    mi.description,
    mi.price,
    mi.stock,
    mi.category,
    mi.seller_name,
    mi.created_at,
    mi.updated_at
FROM market_items mi
WHERE mi.is_active = true
ORDER BY mi.category, mi.name;

-- Create view for recent command usage statistics
CREATE OR REPLACE VIEW command_usage_stats AS
SELECT 
    guild_id,
    command_name,
    COUNT(*) as usage_count,
    COUNT(*) FILTER (WHERE success = true) as successful_uses,
    COUNT(*) FILTER (WHERE success = false) as failed_uses,
    AVG(execution_time_ms) as avg_execution_time_ms,
    MAX(used_at) as last_used
FROM command_usage 
WHERE used_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY guild_id, command_name
ORDER BY usage_count DESC;

-- Update existing loans table to match new requirements
DO $$
BEGIN
    -- Add username column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'loans' AND column_name = 'username') THEN
        ALTER TABLE loans ADD COLUMN username VARCHAR(100);
    END IF;
    
    -- Add issued_date and due_date as varchar if they don't exist as ISO strings
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'loans' AND column_name = 'issued_date_iso') THEN
        ALTER TABLE loans ADD COLUMN issued_date_iso VARCHAR(30);
        ALTER TABLE loans ADD COLUMN due_date_iso VARCHAR(30);
    END IF;
END $$;

-- Create function to automatically update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
DROP TRIGGER IF EXISTS update_market_items_updated_at ON market_items;
CREATE TRIGGER update_market_items_updated_at 
    BEFORE UPDATE ON market_items 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_bot_config_updated_at ON bot_config;
CREATE TRIGGER update_bot_config_updated_at 
    BEFORE UPDATE ON bot_config 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
