#!/usr/bin/env python3
"""
Run the schema consistency fix migration.
This script applies the 05_fix_event_schema_consistency.sql migration.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config.settings import get_database_url
from database.connection import resolve_database_url
import psycopg2

def run_schema_fix():
    """Apply the schema consistency fix migration."""
    
    # Get database URL
    db_url = get_database_url()
    if not db_url:
        print("❌ No database URL available")
        return False
    
    # Resolve URL for connection
    resolved_url = resolve_database_url(db_url)
    
    # Read migration file
    migration_file = Path(__file__).parent / "05_fix_event_schema_consistency.sql"
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    print(f"🔍 Running schema consistency fix migration...")
    print(f"📁 Migration file: {migration_file}")
    print(f"🔗 Database: {db_url[:50]}...")
    
    try:
        # Connect and run migration
        conn = psycopg2.connect(resolved_url)
        
        with conn.cursor() as cursor:
            # Execute migration
            cursor.execute(migration_sql)
            conn.commit()
            
            print("✅ Schema consistency fix applied successfully!")
            
            # Run verification queries
            print("\n🔍 Verifying migration results...")
            
            # Check events table columns
            cursor.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'events' 
                AND column_name IN ('name', 'is_active', 'event_name', 'id', 'guild_id')
                ORDER BY column_name
            """)
            
            columns = cursor.fetchall()
            print("📋 Events table columns:")
            for col in columns:
                print(f"  • {col[0]}: {col[1]} ({'nullable' if col[2] == 'YES' else 'not null'})")
            
            # Check foreign key constraints
            cursor.execute("""
                SELECT constraint_name, table_name, column_name
                FROM information_schema.key_column_usage kcu
                WHERE kcu.table_name = 'mining_participation'
                AND kcu.column_name = 'event_id'
            """)
            
            constraints = cursor.fetchall()
            print("\n🔗 Mining participation constraints:")
            for constraint in constraints:
                print(f"  • {constraint[0]}: {constraint[1]}.{constraint[2]}")
            
            # Test unified view
            cursor.execute("SELECT COUNT(*) FROM unified_events")
            view_count = cursor.fetchone()[0]
            print(f"\n📊 Unified events view: {view_count} total events")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 Red Legion Bot - Schema Consistency Fix")
    print("=" * 50)
    
    success = run_schema_fix()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("🎯 The following issues have been resolved:")
        print("  • Added 'name' column to events table")
        print("  • Added 'is_active' column to events table") 
        print("  • Fixed mining_participation foreign key references")
        print("  • Created unified_events view for compatibility")
        print("  • Added guild_id normalization function")
        print("\n📝 Next steps:")
        print("  1. Test Sunday Mining start/stop commands")
        print("  2. Verify database event creation works")
        print("  3. Check participation tracking")
    else:
        print("\n❌ Migration failed!")
        print("🔧 Please check the error messages above and fix any issues.")
        sys.exit(1)