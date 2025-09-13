-- Migration 15: Salvage Support Tables
-- Adds database tables to support salvage operations and pricing

-- Create salvage components pricing table
CREATE TABLE IF NOT EXISTS salvage_prices (
    id SERIAL PRIMARY KEY,
    component_name VARCHAR(100) NOT NULL,
    price_per_unit DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    best_sell_location VARCHAR(100),
    system_location VARCHAR(50) DEFAULT 'Stanton',
    item_category VARCHAR(50) DEFAULT 'salvage',
    fetched_at TIMESTAMP DEFAULT NOW(),
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Unique constraint for current prices per component
    UNIQUE(component_name, item_category) DEFERRABLE INITIALLY DEFERRED
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_salvage_prices_component_current 
ON salvage_prices(component_name, is_current);

CREATE INDEX IF NOT EXISTS idx_salvage_prices_fetched_at 
ON salvage_prices(fetched_at DESC);

-- Create salvage inventory tracking table (optional for detailed tracking)
CREATE TABLE IF NOT EXISTS salvage_inventory (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(50) REFERENCES events(event_id) ON DELETE CASCADE,
    component_name VARCHAR(100) NOT NULL,
    quantity DECIMAL(10,3) NOT NULL DEFAULT 0,
    estimated_value DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    unit_price DECIMAL(10,2),
    notes TEXT,
    recorded_at TIMESTAMP DEFAULT NOW(),
    recorded_by_id VARCHAR(100),
    recorded_by_name VARCHAR(100)
);

-- Create index for salvage inventory lookups
CREATE INDEX IF NOT EXISTS idx_salvage_inventory_event 
ON salvage_inventory(event_id);

CREATE INDEX IF NOT EXISTS idx_salvage_inventory_component 
ON salvage_inventory(component_name);

-- Insert default salvage component prices (placeholder values)
INSERT INTO salvage_prices (component_name, price_per_unit, best_sell_location, system_location) VALUES
('RCS Thruster', 150.00, 'Area18', 'Stanton'),
('Quantum Drive', 2500.00, 'Port Olisar', 'Stanton'),
('Power Plant', 800.00, 'Lorville', 'Stanton'),
('Shield Generator', 450.00, 'Area18', 'Stanton'),
('Cooler', 200.00, 'Port Olisar', 'Stanton'),
('Scanner', 300.00, 'Area18', 'Stanton'),
('Weapon Mount', 180.00, 'Lorville', 'Stanton'),
('Hull Panel', 75.00, 'Area18', 'Stanton'),
('Wiring Harness', 95.00, 'Port Olisar', 'Stanton'),
('Computer Core', 650.00, 'Area18', 'Stanton')
ON CONFLICT (component_name) DO NOTHING;

-- Update events table to ensure salvage event_type is properly supported
-- (This should already be supported but adding for completeness)
ALTER TABLE events 
ADD CONSTRAINT chk_event_type 
CHECK (event_type IN ('mining', 'salvage', 'transport', 'combat', 'exploration', 'system'));

-- Create comment for documentation
COMMENT ON TABLE salvage_prices IS 'Stores pricing data for salvageable components with location information';
COMMENT ON TABLE salvage_inventory IS 'Optional detailed tracking of salvaged components per event';