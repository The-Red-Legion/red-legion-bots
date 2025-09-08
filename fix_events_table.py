#!/usr/bin/env python3
"""
Fix missing events table in database
This script adds the missing 'events' table that the /testdata command requires.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def fix_events_table():
    """Add the missing events table to the database."""
    try:
        # Import database functionality
        from src.database.connection import initialize_database, DatabaseManager
        from src.config.settings import get_database_url
        
        # Get database URL
        db_url = get_database_url()
        if not db_url:
            print("❌ No database URL found in configuration")
            return False
        
        print("🔧 Connecting to database...")
        
        # Initialize database connection
        db_manager = initialize_database(db_url)
        
        with db_manager.get_cursor() as cursor:
            print("🔍 Checking if events table exists...")
            
            # Check if events table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'events'
                );
            """)
            
            table_exists = cursor.fetchone()[0]
            
            if table_exists:
                # Check if it has the required 'id' column
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'events' AND column_name = 'id' AND table_schema = 'public'
                """)
                
                has_id_column = cursor.fetchone() is not None
                
                if has_id_column:
                    print("✅ Events table already exists with proper schema!")
                    return True
                else:
                    print("⚠️ Events table exists but missing 'id' column")
            
            print("🔧 Creating events table with proper schema...")
            
            # Create the events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    event_date DATE NOT NULL,
                    event_time TIMESTAMP NOT NULL,
                    event_name TEXT DEFAULT 'Sunday Mining',
                    total_participants INTEGER DEFAULT 0,
                    total_payout REAL,
                    is_open BOOLEAN DEFAULT TRUE,
                    payroll_calculated BOOLEAN DEFAULT FALSE,
                    pdf_generated BOOLEAN DEFAULT FALSE,
                    -- Legacy columns for backward compatibility
                    event_id INTEGER GENERATED ALWAYS AS (id) STORED,
                    channel_id TEXT,
                    channel_name TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    total_value REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_guild_id ON events(guild_id);
                CREATE INDEX IF NOT EXISTS idx_events_event_date ON events(event_date);
                CREATE INDEX IF NOT EXISTS idx_events_is_open ON events(is_open);
            """)
            
            print("✅ Events table created successfully!")
            
            # Verify the table was created correctly
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'events' AND column_name = 'id' AND table_schema = 'public'
            """)
            
            if cursor.fetchone():
                print("✅ Verified: Events table has required 'id' column")
                return True
            else:
                print("❌ Failed to create events table properly")
                return False
                
    except Exception as e:
        print(f"❌ Error fixing events table: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Red Legion Bot - Fix Events Table")
    print("=" * 50)
    
    success = fix_events_table()
    
    if success:
        print("\n✅ Events table fix completed successfully!")
        print("You can now try the /testdata command again.")
    else:
        print("\n❌ Events table fix failed!")
        print("Please check the error messages above.")
    
    sys.exit(0 if success else 1)
