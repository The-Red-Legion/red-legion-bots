-- Migration 16: Add trading locations and material pricing system
-- This migration adds support for location-based pricing for materials

-- Create trading locations table
CREATE TABLE IF NOT EXISTS trading_locations (
    location_id SERIAL PRIMARY KEY,
    location_name VARCHAR(100) NOT NULL UNIQUE,
    system_name VARCHAR(50) NOT NULL,
    planet_moon VARCHAR(50),
    station_outpost VARCHAR(100),
    location_type VARCHAR(20) CHECK (location_type IN ('station', 'outpost', 'city', 'settlement')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trading_locations_system ON trading_locations(system_name);
CREATE INDEX IF NOT EXISTS idx_trading_locations_active ON trading_locations(is_active);

-- Create material prices table linking materials to locations
CREATE TABLE IF NOT EXISTS material_prices (
    price_id SERIAL PRIMARY KEY,
    material_id INTEGER REFERENCES materials(material_id) ON DELETE CASCADE,
    location_id INTEGER REFERENCES trading_locations(location_id) ON DELETE CASCADE,
    buy_price NUMERIC(8,2),
    sell_price NUMERIC(8,2) NOT NULL,
    is_current BOOLEAN DEFAULT true,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(material_id, location_id)
);

CREATE INDEX IF NOT EXISTS idx_material_prices_current ON material_prices(is_current, material_id);
CREATE INDEX IF NOT EXISTS idx_material_prices_location ON material_prices(location_id);
CREATE INDEX IF NOT EXISTS idx_material_prices_updated ON material_prices(last_updated);

-- Insert common Star Citizen trading locations
INSERT INTO trading_locations (location_name, system_name, planet_moon, station_outpost, location_type) VALUES
('Area18', 'Stanton', 'ArcCorp', 'Area18', 'city'),
('Lorville', 'Stanton', 'Hurston', 'Lorville', 'city'),
('New Babbage', 'Stanton', 'microTech', 'New Babbage', 'city'),
('Orison', 'Stanton', 'Crusader', 'Orison', 'city'),
('Port Olisar', 'Stanton', NULL, 'Port Olisar', 'station'),
('Everus Harbor', 'Stanton', 'Hurston', 'Everus Harbor', 'station'),
('Baijini Point', 'Stanton', 'microTech', 'Baijini Point', 'station'),
('Seraphim Station', 'Stanton', 'Crusader', 'Seraphim Station', 'station'),
('Tressler', 'Stanton', 'microTech', 'Tressler', 'station'),
('HUR-L1', 'Stanton', NULL, 'HUR-L1 Shallow Fields Station', 'station'),
('CRU-L1', 'Stanton', NULL, 'CRU-L1 Ambitious Dream Station', 'station'),
('MIC-L1', 'Stanton', NULL, 'MIC-L1 Shallow Frontier Station', 'station'),
('ARC-L1', 'Stanton', NULL, 'ARC-L1 Lively Pathway Station', 'station')
ON CONFLICT (location_name) DO NOTHING;

-- Populate materials table with mining ores and salvage materials
INSERT INTO materials (name, category, base_value, rarity, description) VALUES
-- Mining Ores
('Quantainium', 'ore', 8.80, 'Very Rare', 'Highly valuable and unstable quantum-sensitive mineral'),
('Bexalite', 'ore', 7.95, 'Very Rare', 'Rare crystalline structure used in advanced electronics'),
('Taranite', 'ore', 6.20, 'Rare', 'Dense metallic ore with high industrial value'),
('Laranite', 'ore', 3.11, 'Rare', 'Valuable mineral used in high-tech manufacturing'),
('Borase', 'ore', 2.65, 'Uncommon', 'Industrial mineral with moderate value'),
('Agricium', 'ore', 2.13, 'Uncommon', 'Agricultural enhancement mineral'),
('Hephaestanite', 'ore', 2.10, 'Uncommon', 'Heat-resistant mineral for industrial applications'),
('Titanium', 'ore', 1.80, 'Common', 'Lightweight, strong metallic ore'),
('Diamond', 'ore', 1.50, 'Common', 'Crystalline carbon for cutting and industrial use'),
('Gold', 'ore', 1.20, 'Common', 'Precious metal with various applications'),
('Copper', 'ore', 1.10, 'Common', 'Conductive metal ore'),
('Beryl', 'ore', 0.90, 'Common', 'Semi-precious mineral'),
('Tungsten', 'ore', 0.80, 'Common', 'Dense metallic ore for industrial use'),
('Corundum', 'ore', 0.75, 'Common', 'Hard crystalline mineral'),
('Quartz', 'ore', 0.70, 'Common', 'Common silicate mineral'),
('Aluminum', 'ore', 0.65, 'Common', 'Lightweight metallic ore'),
-- Salvage Materials (RMC)
('Recycled Material Composite', 'salvage_rmc', 2.00, 'Common', 'Processed salvaged materials ready for reuse'),
-- Construction Materials  
('Reinforced Metal Salvage', 'salvage_construction', 1.85, 'Common', 'Sturdy metal components from salvaged ships'),
('Processed Scrap Metal', 'salvage_construction', 1.60, 'Common', 'Refined metal from salvage operations'),
('Electronic Components', 'salvage_construction', 2.20, 'Uncommon', 'Salvaged electronic parts and circuits'),
('Composite Paneling', 'salvage_construction', 1.95, 'Common', 'Lightweight panels from ship hulls'),
('Structural Elements', 'salvage_construction', 1.70, 'Common', 'Support structures and framework pieces')
ON CONFLICT (name) DO NOTHING;

-- Insert sample pricing data for key materials at different locations
WITH material_location_prices AS (
    SELECT 
        m.material_id,
        tl.location_id,
        m.name,
        tl.location_name,
        CASE 
            WHEN m.name = 'Quantainium' THEN 
                CASE tl.location_name 
                    WHEN 'Area18' THEN 9.20 
                    WHEN 'Lorville' THEN 9.15 
                    WHEN 'New Babbage' THEN 9.10 
                    WHEN 'Orison' THEN 9.25 
                    ELSE 8.80 
                END
            WHEN m.name = 'Bexalite' THEN 
                CASE tl.location_name 
                    WHEN 'Area18' THEN 8.30 
                    WHEN 'Lorville' THEN 8.25 
                    WHEN 'New Babbage' THEN 8.35 
                    ELSE 7.95 
                END
            WHEN m.name = 'Laranite' THEN 
                CASE tl.location_name 
                    WHEN 'Area18' THEN 3.25 
                    WHEN 'Lorville' THEN 3.30 
                    WHEN 'New Babbage' THEN 3.20 
                    WHEN 'Orison' THEN 3.15 
                    ELSE 3.11 
                END
            WHEN m.name = 'Titanium' THEN 
                CASE tl.location_name 
                    WHEN 'Area18' THEN 1.95 
                    WHEN 'Lorville' THEN 1.90 
                    WHEN 'New Babbage' THEN 1.85 
                    ELSE 1.80 
                END
            WHEN m.name = 'Recycled Material Composite' THEN 
                CASE tl.location_name 
                    WHEN 'Area18' THEN 2.15 
                    WHEN 'Lorville' THEN 2.20 
                    WHEN 'New Babbage' THEN 2.10 
                    ELSE 2.00 
                END
            WHEN m.name = 'Electronic Components' THEN 
                CASE tl.location_name 
                    WHEN 'Area18' THEN 2.35 
                    WHEN 'New Babbage' THEN 2.40 
                    WHEN 'Lorville' THEN 2.30 
                    ELSE 2.20 
                END
            ELSE m.base_value * (1 + random() * 0.3 - 0.15) -- Add some variation to base prices
        END as sell_price
    FROM materials m
    CROSS JOIN trading_locations tl
    WHERE m.is_active = true AND tl.is_active = true
    AND m.name IN ('Quantainium', 'Bexalite', 'Laranite', 'Titanium', 'Diamond', 'Gold', 
                   'Recycled Material Composite', 'Electronic Components', 'Reinforced Metal Salvage')
)
INSERT INTO material_prices (material_id, location_id, sell_price)
SELECT material_id, location_id, sell_price
FROM material_location_prices
ON CONFLICT (material_id, location_id) DO UPDATE SET
    sell_price = EXCLUDED.sell_price,
    last_updated = CURRENT_TIMESTAMP;