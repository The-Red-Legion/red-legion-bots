#!/usr/bin/env python3
"""
Fix events table schema to ensure it has the required 'id' column.
This script will check the current schema and add missing columns if needed.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import get_database_url
import psycopg2

def check_and_fix_events_table():
    """Check events table schema and fix if needed."""
    
    try:
        database_url = get_database_url()
        print(f"🔗 Connecting to database...")
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check current events table schema
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'events' AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        
        current_columns = cursor.fetchall()
        print("🔍 Current events table schema:")
        
        column_names = []
        for row in current_columns:
            column_names.append(row[0])
            print(f"  📋 {row[0]}: {row[1]} (nullable: {row[2]}, default: {row[3]})")
        
        # Check if 'id' column exists
        has_id_column = 'id' in column_names
        
        if not has_id_column:
            print("\n❌ Missing 'id' column in events table!")
            print("🔧 This needs to be fixed to support test data management...")
            
            # Check if there's any data in the table
            cursor.execute("SELECT COUNT(*) FROM events")
            row_count = cursor.fetchone()[0]
            print(f"📊 Current events table has {row_count} rows")
            
            if row_count == 0:
                print("🗑️ Table is empty, we can safely recreate it...")
                
                # Drop and recreate the table with proper schema
                cursor.execute("DROP TABLE IF EXISTS events CASCADE")
                print("✅ Dropped old events table")
                
                # Create new events table with proper schema
                cursor.execute("""
                    CREATE TABLE events (
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
                    )
                """)
                print("✅ Created new events table with proper schema")
                
            else:
                print("⚠️ Table has data, need to migrate carefully...")
                print("🚨 This requires manual intervention to preserve data!")
                print("📝 Suggested steps:")
                print("   1. Backup existing events data")
                print("   2. Create new table with proper schema")
                print("   3. Migrate data from old table to new table")
                print("   4. Update any references")
                return False
                
        else:
            print("✅ Events table has 'id' column - schema looks good!")
            
        # Check if mining_participation table references are correct
        if has_id_column:
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_name = 'mining_participation' AND column_name = 'event_id'
            """)
            
            part_event_id = cursor.fetchone()
            if part_event_id:
                print(f"✅ mining_participation.event_id exists: {part_event_id[1]}")
            else:
                print("⚠️ mining_participation table missing event_id column")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 Database schema check completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error checking database schema: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Red Legion Bot - Events Table Schema Fix")
    print("=" * 50)
    
    success = check_and_fix_events_table()
    
    if success:
        print("\n✅ Schema fix completed successfully!")
    else:
        print("\n❌ Schema fix failed - manual intervention required")
        sys.exit(1)
