-- Migration: Market System for /red-market subcommands
-- Date: September 8, 2025
-- Purpose: Support trading marketplace with listings, transactions, and category management

-- Market listings table
CREATE TABLE IF NOT EXISTS market_listings (
    listing_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    seller_id VARCHAR(20),
    seller_name VARCHAR(100),
    
    -- Item details
    item_name VARCHAR(200) NOT NULL,
    item_description TEXT,
    item_category VARCHAR(50) DEFAULT 'misc',
    item_subcategory VARCHAR(50),
    item_condition VARCHAR(20) DEFAULT 'new' CHECK (item_condition IN ('new', 'used', 'refurbished', 'damaged')),
    
    -- Pricing and quantity
    price_uec DECIMAL(15,2) NOT NULL CHECK (price_uec > 0),
    original_price_uec DECIMAL(15,2),
    quantity INTEGER DEFAULT 1 CHECK (quantity > 0),
    quantity_sold INTEGER DEFAULT 0,
    
    -- Location and logistics
    location_system VARCHAR(100),
    location_planet VARCHAR(100),
    location_station VARCHAR(100),
    delivery_available BOOLEAN DEFAULT FALSE,
    delivery_cost_uec DECIMAL(10,2) DEFAULT 0,
    
    -- Status and metadata
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'sold', 'expired', 'removed')),
    featured BOOLEAN DEFAULT FALSE,
    bump_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    sold_at TIMESTAMP,
    last_bumped_at TIMESTAMP
);

-- Market categories lookup table
CREATE TABLE IF NOT EXISTS market_categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_category VARCHAR(50),
    icon_emoji VARCHAR(50),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    requires_verification BOOLEAN DEFAULT FALSE
);

-- Market transactions table
CREATE TABLE IF NOT EXISTS market_transactions (
    transaction_id SERIAL PRIMARY KEY,
    listing_id INTEGER REFERENCES market_listings(listing_id) ON DELETE CASCADE,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    
    -- Parties involved
    seller_id VARCHAR(20),
    seller_name VARCHAR(100),
    buyer_id VARCHAR(20),
    buyer_name VARCHAR(100),
    
    -- Transaction details
    item_name VARCHAR(200),
    quantity_purchased INTEGER NOT NULL CHECK (quantity_purchased > 0),
    unit_price_uec DECIMAL(15,2) NOT NULL,
    total_price_uec DECIMAL(15,2) NOT NULL,
    delivery_cost_uec DECIMAL(10,2) DEFAULT 0,
    
    -- Transaction status
    transaction_status VARCHAR(20) DEFAULT 'pending' CHECK (transaction_status IN ('pending', 'confirmed', 'completed', 'cancelled', 'disputed')),
    payment_method VARCHAR(30),
    payment_status VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'refunded')),
    
    -- Delivery tracking
    delivery_status VARCHAR(20) DEFAULT 'not_started' CHECK (delivery_status IN ('not_started', 'in_transit', 'delivered', 'failed')),
    delivery_location VARCHAR(200),
    delivery_notes TEXT,
    
    -- Timestamps
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_date TIMESTAMP,
    delivery_date TIMESTAMP,
    completed_date TIMESTAMP
);

-- Market settings per guild
CREATE TABLE IF NOT EXISTS market_settings (
    setting_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    
    -- Channel configuration
    market_channel_id VARCHAR(20),
    transaction_log_channel_id VARCHAR(20),
    moderator_role_id VARCHAR(20),
    
    -- Listing settings
    max_listings_per_user INTEGER DEFAULT 10,
    listing_duration_days INTEGER DEFAULT 30,
    auto_bump_enabled BOOLEAN DEFAULT TRUE,
    bump_cooldown_hours INTEGER DEFAULT 24,
    require_approval BOOLEAN DEFAULT FALSE,
    
    -- Pricing settings
    min_price_uec DECIMAL(10,2) DEFAULT 1.00,
    max_price_uec DECIMAL(15,2) DEFAULT 10000000.00,
    transaction_fee_percent DECIMAL(5,2) DEFAULT 0.00,
    
    -- Features
    delivery_tracking_enabled BOOLEAN DEFAULT TRUE,
    reputation_system_enabled BOOLEAN DEFAULT TRUE,
    featured_listings_enabled BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id)
);

-- Market favorites/watchlist
CREATE TABLE IF NOT EXISTS market_favorites (
    favorite_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    user_id VARCHAR(20),
    username VARCHAR(100),
    listing_id INTEGER REFERENCES market_listings(listing_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, user_id, listing_id)
);

-- User market reputation (for future features)
CREATE TABLE IF NOT EXISTS market_reputation (
    reputation_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    user_id VARCHAR(20),
    username VARCHAR(100),
    
    -- Reputation metrics
    total_sales INTEGER DEFAULT 0,
    total_purchases INTEGER DEFAULT 0,
    successful_transactions INTEGER DEFAULT 0,
    disputed_transactions INTEGER DEFAULT 0,
    
    -- Ratings
    average_seller_rating DECIMAL(3,2) DEFAULT 0.00,
    average_buyer_rating DECIMAL(3,2) DEFAULT 0.00,
    total_seller_reviews INTEGER DEFAULT 0,
    total_buyer_reviews INTEGER DEFAULT 0,
    
    -- Trust score (calculated field)
    trust_score INTEGER DEFAULT 50 CHECK (trust_score >= 0 AND trust_score <= 100),
    
    -- Status
    is_verified_trader BOOLEAN DEFAULT FALSE,
    is_blacklisted BOOLEAN DEFAULT FALSE,
    blacklist_reason TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, user_id)
);

-- Indexes for market operations
CREATE INDEX IF NOT EXISTS idx_market_listings_guild ON market_listings(guild_id);
CREATE INDEX IF NOT EXISTS idx_market_listings_seller ON market_listings(seller_id);
CREATE INDEX IF NOT EXISTS idx_market_listings_category ON market_listings(item_category);
CREATE INDEX IF NOT EXISTS idx_market_listings_status ON market_listings(status);
CREATE INDEX IF NOT EXISTS idx_market_listings_price ON market_listings(price_uec);
CREATE INDEX IF NOT EXISTS idx_market_listings_created ON market_listings(created_at);
CREATE INDEX IF NOT EXISTS idx_market_listings_expires ON market_listings(expires_at);
CREATE INDEX IF NOT EXISTS idx_market_listings_featured ON market_listings(featured);

CREATE INDEX IF NOT EXISTS idx_market_transactions_listing ON market_transactions(listing_id);
CREATE INDEX IF NOT EXISTS idx_market_transactions_seller ON market_transactions(seller_id);
CREATE INDEX IF NOT EXISTS idx_market_transactions_buyer ON market_transactions(buyer_id);
CREATE INDEX IF NOT EXISTS idx_market_transactions_status ON market_transactions(transaction_status);
CREATE INDEX IF NOT EXISTS idx_market_transactions_date ON market_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_market_transactions_guild ON market_transactions(guild_id);

CREATE INDEX IF NOT EXISTS idx_market_favorites_user ON market_favorites(guild_id, user_id);
CREATE INDEX IF NOT EXISTS idx_market_favorites_listing ON market_favorites(listing_id);

CREATE INDEX IF NOT EXISTS idx_market_reputation_guild_user ON market_reputation(guild_id, user_id);
CREATE INDEX IF NOT EXISTS idx_market_reputation_trust_score ON market_reputation(trust_score);
CREATE INDEX IF NOT EXISTS idx_market_reputation_verified ON market_reputation(is_verified_trader);

-- Insert standard market categories
INSERT INTO market_categories (category_name, display_name, description, icon_emoji, sort_order) 
VALUES 
    ('ships', 'Ships & Vehicles', 'Spacecraft, ground vehicles, and other transportation', '🚀', 1),
    ('components', 'Ship Components', 'Weapons, shields, power plants, and other ship parts', '⚙️', 2),
    ('weapons', 'Weapons & Equipment', 'Personal weapons, armor, and combat equipment', '⚔️', 3),
    ('cargo', 'Cargo & Resources', 'Raw materials, refined goods, and trade commodities', '📦', 4),
    ('services', 'Services', 'Transport, escort, mining, and other professional services', '🛠️', 5),
    ('consumables', 'Consumables', 'Food, medical supplies, fuel, and other consumables', '🍃', 6),
    ('misc', 'Miscellaneous', 'Other items and collectibles', '📋', 7)
ON CONFLICT (category_name) DO NOTHING;

-- Create views for market data
CREATE OR REPLACE VIEW active_market_listings AS
SELECT 
    l.listing_id,
    l.guild_id,
    l.seller_id,
    l.seller_name,
    l.item_name,
    l.item_description,
    l.item_category,
    c.display_name as category_display,
    c.icon_emoji as category_icon,
    l.price_uec,
    l.quantity,
    l.quantity_sold,
    (l.quantity - l.quantity_sold) as quantity_available,
    l.location_system,
    l.location_planet,
    l.delivery_available,
    l.delivery_cost_uec,
    l.featured,
    l.view_count,
    l.created_at,
    l.expires_at,
    EXTRACT(days FROM (l.expires_at - CURRENT_TIMESTAMP)) as days_until_expiry,
    (SELECT COUNT(*) FROM market_favorites f WHERE f.listing_id = l.listing_id) as favorite_count
FROM market_listings l
LEFT JOIN market_categories c ON l.item_category = c.category_name
WHERE l.status = 'active' 
  AND (l.expires_at IS NULL OR l.expires_at > CURRENT_TIMESTAMP)
  AND l.quantity > l.quantity_sold;

CREATE OR REPLACE VIEW market_statistics AS
SELECT 
    l.guild_id,
    COUNT(*) as total_active_listings,
    COUNT(DISTINCT l.seller_id) as unique_sellers,
    COUNT(*) FILTER (WHERE l.featured = true) as featured_listings,
    COUNT(*) FILTER (WHERE l.created_at >= CURRENT_DATE - INTERVAL '7 days') as listings_last_7_days,
    COUNT(*) FILTER (WHERE l.created_at >= CURRENT_DATE - INTERVAL '30 days') as listings_last_30_days,
    AVG(l.price_uec) as average_price,
    MIN(l.price_uec) as min_price,
    MAX(l.price_uec) as max_price,
    SUM(l.quantity - l.quantity_sold) as total_items_available,
    COUNT(*) FILTER (WHERE l.expires_at <= CURRENT_TIMESTAMP + INTERVAL '7 days') as expiring_soon
FROM market_listings l
WHERE l.status = 'active'
GROUP BY l.guild_id;

CREATE OR REPLACE VIEW transaction_summary AS
SELECT 
    t.guild_id,
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE t.transaction_status = 'completed') as completed_transactions,
    COUNT(*) FILTER (WHERE t.transaction_status = 'pending') as pending_transactions,
    COUNT(*) FILTER (WHERE t.transaction_date >= CURRENT_DATE - INTERVAL '30 days') as transactions_last_30_days,
    SUM(t.total_price_uec) FILTER (WHERE t.transaction_status = 'completed') as total_volume_uec,
    AVG(t.total_price_uec) FILTER (WHERE t.transaction_status = 'completed') as average_transaction_value,
    COUNT(DISTINCT t.seller_id) as unique_sellers,
    COUNT(DISTINCT t.buyer_id) as unique_buyers
FROM market_transactions t
GROUP BY t.guild_id;

-- Insert default market settings for existing guilds
INSERT INTO market_settings (guild_id, max_listings_per_user, listing_duration_days, auto_bump_enabled, require_approval)
SELECT DISTINCT guild_id, 10, 30, true, false
FROM guilds
ON CONFLICT (guild_id) DO NOTHING;

-- Function to automatically update listing status
CREATE OR REPLACE FUNCTION update_expired_listings()
RETURNS VOID AS $$
BEGIN
    -- Mark expired listings as expired
    UPDATE market_listings 
    SET status = 'expired', updated_at = CURRENT_TIMESTAMP
    WHERE status = 'active' 
      AND expires_at IS NOT NULL 
      AND expires_at <= CURRENT_TIMESTAMP;
    
    -- Mark fully sold listings as sold
    UPDATE market_listings 
    SET status = 'sold', updated_at = CURRENT_TIMESTAMP, sold_at = CURRENT_TIMESTAMP
    WHERE status = 'active' 
      AND quantity <= quantity_sold;
END;
$$ LANGUAGE plpgsql;

-- Function to update market reputation after transaction
CREATE OR REPLACE FUNCTION update_market_reputation(
    p_guild_id VARCHAR(20),
    p_seller_id VARCHAR(20),
    p_buyer_id VARCHAR(20),
    p_transaction_successful BOOLEAN
)
RETURNS VOID AS $$
BEGIN
    -- Update seller reputation
    INSERT INTO market_reputation (guild_id, user_id, total_sales, successful_transactions)
    VALUES (p_guild_id, p_seller_id, 1, CASE WHEN p_transaction_successful THEN 1 ELSE 0 END)
    ON CONFLICT (guild_id, user_id) 
    DO UPDATE SET 
        total_sales = market_reputation.total_sales + 1,
        successful_transactions = market_reputation.successful_transactions + CASE WHEN p_transaction_successful THEN 1 ELSE 0 END,
        disputed_transactions = market_reputation.disputed_transactions + CASE WHEN NOT p_transaction_successful THEN 1 ELSE 0 END,
        updated_at = CURRENT_TIMESTAMP;
    
    -- Update buyer reputation
    INSERT INTO market_reputation (guild_id, user_id, total_purchases, successful_transactions)
    VALUES (p_guild_id, p_buyer_id, 1, CASE WHEN p_transaction_successful THEN 1 ELSE 0 END)
    ON CONFLICT (guild_id, user_id) 
    DO UPDATE SET 
        total_purchases = market_reputation.total_purchases + 1,
        successful_transactions = market_reputation.successful_transactions + CASE WHEN p_transaction_successful THEN 1 ELSE 0 END,
        disputed_transactions = market_reputation.disputed_transactions + CASE WHEN NOT p_transaction_successful THEN 1 ELSE 0 END,
        updated_at = CURRENT_TIMESTAMP;
    
    -- Recalculate trust scores
    UPDATE market_reputation 
    SET trust_score = LEAST(100, GREATEST(0, 
        50 + (successful_transactions * 2) - (disputed_transactions * 5)
    ))
    WHERE guild_id = p_guild_id AND user_id IN (p_seller_id, p_buyer_id);
END;
$$ LANGUAGE plpgsql;

-- Trigger to set expiry date on new listings
CREATE OR REPLACE FUNCTION set_listing_expiry()
RETURNS TRIGGER AS $$
DECLARE
    default_duration INTEGER;
BEGIN
    -- Get default listing duration for the guild
    SELECT listing_duration_days INTO default_duration
    FROM market_settings 
    WHERE guild_id = NEW.guild_id;
    
    -- If no guild settings, use 30 days default
    IF default_duration IS NULL THEN
        default_duration := 30;
    END IF;
    
    -- Set expiry date if not provided
    IF NEW.expires_at IS NULL THEN
        NEW.expires_at := CURRENT_TIMESTAMP + (default_duration || ' days')::INTERVAL;
    END IF;
    
    -- Set updated timestamp
    NEW.updated_at := CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_set_listing_expiry ON market_listings;
CREATE TRIGGER trigger_set_listing_expiry
    BEFORE INSERT OR UPDATE ON market_listings
    FOR EACH ROW
    EXECUTE FUNCTION set_listing_expiry();