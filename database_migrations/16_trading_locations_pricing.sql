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
('ARC-L1', 'Stanton', NULL, 'ARC-L1 Lively Pathway Station', 'station'),
-- Pyro System Locations
('Ruin Station', 'Pyro', 'Pyro I', 'Ruin Station', 'station'),
('Checkmate Station', 'Pyro', 'Pyro III', 'Checkmate Station', 'station'),
('Shady Glen', 'Pyro', 'Pyro IV', 'Shady Glen', 'outpost'),
('Pyro Station', 'Pyro', 'Pyro VI', 'Pyro Station', 'station'),
('Terminus', 'Pyro', 'Pyro VI', 'Terminus', 'outpost')
ON CONFLICT (location_name) DO NOTHING;

-- Populate materials table with mining ores and salvage materials
INSERT INTO materials (name, category, base_value, rarity, description) VALUES
-- Mining Ores (UEX Refined Ore Prices - December 2024)
('QUANTAINIUM', 'ore', 21848.0, 'Very Rare', 'Highly valuable and unstable quantum-sensitive mineral'),
('BEXALITE', 'ore', 6731.0, 'Very Rare', 'Rare crystalline structure used in advanced electronics'),
('TARANITE', 'ore', 8886.0, 'Rare', 'Dense metallic ore with high industrial value'),
('LARANITE', 'ore', 2647.0, 'Rare', 'Valuable mineral used in high-tech manufacturing'),
('BORASE', 'ore', 3028.0, 'Uncommon', 'Industrial mineral with moderate value'),
('AGRICIUM', 'ore', 2366.0, 'Uncommon', 'Agricultural enhancement mineral'),
('HEPHAESTANITE', 'ore', 2340.0, 'Uncommon', 'Heat-resistant mineral for industrial applications'),
('TITANIUM', 'ore', 452.0, 'Common', 'Lightweight, strong metallic ore'),
('DIAMOND', 'ore', 5489.0, 'Common', 'Crystalline carbon for cutting and industrial use'),
('GOLD', 'ore', 5874.0, 'Common', 'Precious metal with various applications'),
('COPPER', 'ore', 350.0, 'Common', 'Conductive metal ore'),
('BERYL', 'ore', 2581.0, 'Common', 'Semi-precious mineral'),
('TUNGSTEN', 'ore', 611.0, 'Common', 'Dense metallic ore for industrial use'),
('CORUNDUM', 'ore', 362.0, 'Common', 'Hard crystalline mineral'),
('QUARTZ', 'ore', 365.0, 'Common', 'Common silicate mineral'),
('ALUMINUM', 'ore', 304.0, 'Common', 'Lightweight metallic ore'),
('IRON', 'ore', 374.0, 'Common', 'Common metallic ore'),
-- Salvage Materials (RMC) - using realistic UEX-based prices
('Recycled Material Composite', 'salvage_rmc', 9869.0, 'Common', 'Processed salvaged materials ready for reuse'),
('Construction Materials', 'salvage_construction', 2157.0, 'Common', 'Mixed construction materials from salvage operations'),
-- Other Construction Materials  
('Reinforced Metal Salvage', 'salvage_construction', 1850.0, 'Common', 'Sturdy metal components from salvaged ships'),
('Processed Scrap Metal', 'salvage_construction', 1600.0, 'Common', 'Refined metal from salvage operations'),
('Electronic Components', 'salvage_construction', 2200.0, 'Uncommon', 'Salvaged electronic parts and circuits'),
('Composite Paneling', 'salvage_construction', 1950.0, 'Common', 'Lightweight panels from ship hulls'),
('Structural Elements', 'salvage_construction', 1700.0, 'Common', 'Support structures and framework pieces')
ON CONFLICT (name) DO NOTHING;

-- Insert sample pricing data for key materials at different locations
WITH material_location_prices AS (
    SELECT 
        m.material_id,
        tl.location_id,
        m.name,
        tl.location_name,
        CASE 
            WHEN m.name = 'QUANTAINIUM' THEN 
                CASE tl.location_name 
                    WHEN 'Area18' THEN 22300.0 
                    WHEN 'Lorville' THEN 22100.0 
                    WHEN 'New Babbage' THEN 21950.0 
                    WHEN 'Orison' THEN 22500.0 
                    ELSE 21848.0 
                END
            WHEN m.name = 'BEXALITE' THEN 
                CASE tl.location_name 
                    WHEN 'Area18' THEN 6850.0 
                    WHEN 'Lorville' THEN 6800.0 
                    WHEN 'New Babbage' THEN 6900.0 
                    ELSE 6731.0 
                END
            WHEN m.name = 'LARANITE' THEN 
                CASE tl.location_name 
                    WHEN 'Area18' THEN 2700.0 
                    WHEN 'Lorville' THEN 2720.0 
                    WHEN 'New Babbage' THEN 2680.0 
                    WHEN 'Orison' THEN 2650.0 
                    ELSE 2647.0 
                END
            WHEN m.name = 'TITANIUM' THEN 
                CASE tl.location_name 
                    WHEN 'Area18' THEN 465.0 
                    WHEN 'Lorville' THEN 460.0 
                    WHEN 'New Babbage' THEN 455.0 
                    ELSE 452.0 
                END
            WHEN m.name = 'TARANITE' THEN 
                CASE tl.location_name 
                    WHEN 'Orison' THEN 9774.60
                    WHEN 'Area18' THEN 9597.28
                    WHEN 'Lorville' THEN 9419.16
                    ELSE 8886.0 
                END
            WHEN m.name = 'HADANITE' THEN 
                CASE tl.location_name 
                    WHEN 'Orison' THEN 25025.0
                    WHEN 'Area18' THEN 24570.0
                    WHEN 'Lorville' THEN 24115.0
                    ELSE 22750.0 
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
    AND m.name IN ('QUANTAINIUM', 'BEXALITE', 'LARANITE', 'TITANIUM', 'DIAMOND', 'GOLD', 
                   'TARANITE', 'BORASE', 'AGRICIUM', 'HEPHAESTANITE', 'BERYL', 'TUNGSTEN', 
                   'COPPER', 'CORUNDUM', 'QUARTZ', 'HADANITE', 'APHORITE', 'DOLIVINE', 
                   'RICCITE', 'ALUMINUM', 'IRON',
                   'Recycled Material Composite', 'Construction Materials', 'Electronic Components', 'Reinforced Metal Salvage')
    AND tl.system_name = 'Stanton'
)
INSERT INTO material_prices (material_id, location_id, sell_price)
SELECT material_id, location_id, sell_price
FROM material_location_prices
ON CONFLICT (material_id, location_id) DO UPDATE SET
    sell_price = EXCLUDED.sell_price,
    last_updated = CURRENT_TIMESTAMP;

-- Add Pyro system pricing data (generally higher prices due to lawless nature)
WITH pyro_material_prices AS (
    SELECT 
        m.material_id,
        tl.location_id,
        CASE 
            WHEN m.name = 'QUANTAINIUM' THEN 
                CASE tl.location_name 
                    WHEN 'Ruin Station' THEN 23500.0
                    WHEN 'Checkmate Station' THEN 23200.0
                    WHEN 'Pyro Station' THEN 23000.0
                    ELSE 22800.0
                END
            WHEN m.name = 'BEXALITE' THEN 
                CASE tl.location_name 
                    WHEN 'Ruin Station' THEN 7200.0
                    WHEN 'Checkmate Station' THEN 7100.0
                    ELSE 6950.0
                END
            WHEN m.name = 'Recycled Material Composite' THEN
                CASE tl.location_name
                    WHEN 'Ruin Station' THEN 2.40
                    WHEN 'Checkmate Station' THEN 2.35
                    ELSE 2.25
                END
            WHEN m.name = 'Electronic Components' THEN
                CASE tl.location_name
                    WHEN 'Ruin Station' THEN 2.50
                    WHEN 'Checkmate Station' THEN 2.45
                    ELSE 2.35
                END
            ELSE m.base_value * 1.15  -- 15% markup for Pyro system
        END as sell_price
    FROM materials m
    CROSS JOIN trading_locations tl
    WHERE m.is_active = true AND tl.system_name = 'Pyro'
    AND m.name IN ('QUANTAINIUM', 'BEXALITE', 'LARANITE', 'TITANIUM', 'TARANITE', 'HADANITE', 'RICCITE', 'APHORITE', 
                   'Recycled Material Composite', 'Construction Materials', 'Electronic Components')
)
INSERT INTO material_prices (material_id, location_id, sell_price)
SELECT material_id, location_id, sell_price
FROM pyro_material_prices
ON CONFLICT (material_id, location_id) DO UPDATE SET
    sell_price = EXCLUDED.sell_price,
    last_updated = CURRENT_TIMESTAMP;