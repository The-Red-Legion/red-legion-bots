#!/usr/bin/env python3
"""
Database Migration: Add Event Management System Columns
Date: 2025-09-08
Purpose: Enhance mining_events table to support comprehensive event management

This script adds the necessary columns to support the new /events command structure
with categories, organizers, status tracking, and enhanced metadata.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_migration():
    """Run the migration to add event management columns."""
    
    try:
        from config.settings import get_database_url
        import psycopg2
        from urllib.parse import urlparse
        
        db_url = get_database_url()
        if not db_url:
            print("❌ No database URL configured")
            return False
        
        print("🔄 Starting event management system migration...")
        
        # Convert database_url to use proxy if running locally
        parsed = urlparse(db_url)
        if parsed.hostname not in ['127.0.0.1', 'localhost']:
            proxy_url = db_url.replace(f'{parsed.hostname}:{parsed.port}', '127.0.0.1:5433')
            try:
                conn = psycopg2.connect(proxy_url)
                print("✅ Connected via Cloud SQL Proxy")
            except psycopg2.OperationalError:
                conn = psycopg2.connect(db_url)
                print("✅ Connected directly to database")
        else:
            conn = psycopg2.connect(db_url)
            print("✅ Connected to local database")
        
        cursor = conn.cursor()
        
        # Step 1: Add new columns
        print("📝 Adding new columns to mining_events table...")
        
        add_columns_sql = """
        -- Add missing columns to mining_events table
        ALTER TABLE mining_events 
        ADD COLUMN IF NOT EXISTS organizer_id VARCHAR(20),
        ADD COLUMN IF NOT EXISTS organizer_name VARCHAR(100),
        ADD COLUMN IF NOT EXISTS event_type VARCHAR(50) DEFAULT 'mining',
        ADD COLUMN IF NOT EXISTS start_time TIMESTAMP,
        ADD COLUMN IF NOT EXISTS end_time TIMESTAMP,
        ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'planned',
        ADD COLUMN IF NOT EXISTS total_value_auec BIGINT;
        """
        
        cursor.execute(add_columns_sql)
        print("✅ New columns added successfully")
        
        # Step 2: Update existing records
        print("🔄 Updating existing records with default values...")
        
        update_existing_sql = """
        UPDATE mining_events 
        SET 
            event_type = COALESCE(event_type, 'mining'),
            status = CASE 
                WHEN status IS NULL THEN
                    CASE 
                        WHEN is_active = true THEN 'active'
                        ELSE 'completed'
                    END
                ELSE status
            END,
            start_time = COALESCE(start_time, created_at, CURRENT_TIMESTAMP)
        WHERE event_type IS NULL OR status IS NULL OR start_time IS NULL;
        """
        
        cursor.execute(update_existing_sql)
        updated_rows = cursor.rowcount
        print(f"✅ Updated {updated_rows} existing records")
        
        # Step 3: Create indexes
        print("📊 Creating indexes for performance...")
        
        create_indexes_sql = """
        CREATE INDEX IF NOT EXISTS idx_mining_events_organizer ON mining_events(organizer_id);
        CREATE INDEX IF NOT EXISTS idx_mining_events_type ON mining_events(event_type);
        CREATE INDEX IF NOT EXISTS idx_mining_events_status ON mining_events(status);
        CREATE INDEX IF NOT EXISTS idx_mining_events_start_time ON mining_events(start_time);
        """
        
        cursor.execute(create_indexes_sql)
        print("✅ Indexes created successfully")
        
        # Step 4: Add constraints (with error handling for existing constraints)
        print("🔒 Adding data validation constraints...")
        
        try:
            constraint_sql = """
            ALTER TABLE mining_events 
            ADD CONSTRAINT chk_event_type 
            CHECK (event_type IN ('mining', 'training', 'combat_operations', 'salvage', 'misc'));
            """
            cursor.execute(constraint_sql)
        except psycopg2.errors.DuplicateObject:
            print("ℹ️ Event type constraint already exists")
        except Exception as e:
            print(f"⚠️ Could not add event type constraint: {e}")
        
        try:
            status_constraint_sql = """
            ALTER TABLE mining_events 
            ADD CONSTRAINT chk_status 
            CHECK (status IN ('planned', 'active', 'completed', 'cancelled'));
            """
            cursor.execute(status_constraint_sql)
        except psycopg2.errors.DuplicateObject:
            print("ℹ️ Status constraint already exists")
        except Exception as e:
            print(f"⚠️ Could not add status constraint: {e}")
        
        # Step 5: Create event categories lookup table
        print("📋 Creating event categories lookup table...")
        
        categories_sql = """
        CREATE TABLE IF NOT EXISTS event_categories (
            category_id SERIAL PRIMARY KEY,
            category_name VARCHAR(50) UNIQUE NOT NULL,
            display_name VARCHAR(100) NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cursor.execute(categories_sql)
        
        # Insert standard categories
        insert_categories_sql = """
        INSERT INTO event_categories (category_name, display_name, description) 
        VALUES 
            ('mining', 'Mining Operations', 'Resource extraction and mining activities'),
            ('training', 'Training Sessions', 'Skills training and educational activities'),
            ('combat_operations', 'Combat Operations', 'Military operations and combat missions'),
            ('salvage', 'Salvage Operations', 'Salvage and recovery missions'),
            ('misc', 'Miscellaneous', 'Other organization events and activities')
        ON CONFLICT (category_name) DO NOTHING;
        """
        
        cursor.execute(insert_categories_sql)
        categories_inserted = cursor.rowcount
        print(f"✅ Event categories table created, {categories_inserted} categories added")
        
        # Step 6: Verify the migration
        print("🔍 Verifying migration...")
        
        verify_sql = """
        SELECT 
            column_name, 
            data_type, 
            is_nullable, 
            column_default
        FROM information_schema.columns 
        WHERE table_name = 'mining_events' 
        AND column_name IN ('organizer_id', 'organizer_name', 'event_type', 'start_time', 'end_time', 'status', 'total_value_auec')
        ORDER BY column_name;
        """
        
        cursor.execute(verify_sql)
        columns = cursor.fetchall()
        
        print("📋 New columns verified:")
        for col in columns:
            print(f"   - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        print("✅ Migration completed successfully!")
        print("🎉 The mining_events table now supports comprehensive event management!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 Red Legion Event Management System Migration")
    print("=" * 50)
    
    success = run_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("🎯 You can now use the enhanced /events commands with:")
        print("   • Event categories (mining, training, combat_ops, salvage, misc)")
        print("   • Organizer tracking") 
        print("   • Status management (planned, active, completed, cancelled)")
        print("   • Enhanced timing and financial tracking")
    else:
        print("\n❌ Migration failed!")
        print("🔧 Please check the error messages above and try again.")
        sys.exit(1)
