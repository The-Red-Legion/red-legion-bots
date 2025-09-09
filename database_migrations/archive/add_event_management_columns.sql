-- Migration: Add Event Management System Columns
-- Date: 2025-09-08
-- Purpose: Enhance mining_events table to support comprehensive event management

-- Add missing columns to mining_events table
ALTER TABLE mining_events 
ADD COLUMN IF NOT EXISTS organizer_id VARCHAR(20),
ADD COLUMN IF NOT EXISTS organizer_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS event_type VARCHAR(50) DEFAULT 'mining',
ADD COLUMN IF NOT EXISTS start_time TIMESTAMP,
ADD COLUMN IF NOT EXISTS end_time TIMESTAMP,
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'planned',
ADD COLUMN IF NOT EXISTS total_value_auec BIGINT;

-- Update existing records to have proper defaults
UPDATE mining_events 
SET 
    event_type = 'mining',
    status = CASE 
        WHEN is_active = true THEN 'active'
        ELSE 'completed'
    END,
    start_time = COALESCE(created_at, CURRENT_TIMESTAMP)
WHERE event_type IS NULL OR status IS NULL;

-- Create indexes for the new columns
CREATE INDEX IF NOT EXISTS idx_mining_events_organizer ON mining_events(organizer_id);
CREATE INDEX IF NOT EXISTS idx_mining_events_type ON mining_events(event_type);
CREATE INDEX IF NOT EXISTS idx_mining_events_status ON mining_events(status);
CREATE INDEX IF NOT EXISTS idx_mining_events_start_time ON mining_events(start_time);

-- Add check constraints for valid values
ALTER TABLE mining_events 
ADD CONSTRAINT chk_event_type 
CHECK (event_type IN ('mining', 'training', 'combat_operations', 'salvage', 'misc'));

ALTER TABLE mining_events 
ADD CONSTRAINT chk_status 
CHECK (status IN ('planned', 'active', 'completed', 'cancelled'));

-- Create event categories lookup table (optional but recommended)
CREATE TABLE IF NOT EXISTS event_categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert standard categories
INSERT INTO event_categories (category_name, display_name, description) 
VALUES 
    ('mining', 'Mining Operations', 'Resource extraction and mining activities'),
    ('training', 'Training Sessions', 'Skills training and educational activities'),
    ('combat_operations', 'Combat Operations', 'Military operations and combat missions'),
    ('salvage', 'Salvage Operations', 'Salvage and recovery missions'),
    ('misc', 'Miscellaneous', 'Other organization events and activities')
ON CONFLICT (category_name) DO NOTHING;
