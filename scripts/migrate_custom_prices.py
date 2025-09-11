#!/usr/bin/env python3
"""
Database migration script to add custom_prices column to payroll_sessions table.
This script uses the bot's existing database configuration to apply the migration.
"""
import asyncio
import asyncpg
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import get_database_url

async def apply_migration():
    """Apply the custom_prices column migration."""
    try:
        # Get database URL using bot's configuration
        db_url = get_database_url()
        print(f"🔗 Connecting to database...")
        
        # Connect to database
        conn = await asyncpg.connect(db_url)
        
        # Read and execute migration
        migration_sql = """
        -- Add custom_prices column to payroll_sessions table for Step 2.5 custom pricing feature
        -- This stores user-defined ore prices that override UEX market prices

        ALTER TABLE payroll_sessions 
        ADD COLUMN IF NOT EXISTS custom_prices JSONB DEFAULT '{}';

        -- Create index for faster queries on custom_prices
        CREATE INDEX IF NOT EXISTS idx_payroll_sessions_custom_prices 
        ON payroll_sessions USING gin(custom_prices);

        -- Add comment for documentation
        COMMENT ON COLUMN payroll_sessions.custom_prices IS 'User-defined ore prices that override UEX market prices in Step 2.5 custom pricing';
        """
        
        print("📝 Applying migration: Add custom_prices column...")
        await conn.execute(migration_sql)
        print("✅ Migration applied successfully!")
        
        # Verify the column exists
        result = await conn.fetchrow("""
            SELECT column_name, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'payroll_sessions' 
            AND column_name = 'custom_prices'
        """)
        
        if result:
            print(f"🔍 Verified column exists: {result['column_name']} ({result['data_type']}) default: {result['column_default']}")
        else:
            print("❌ Column verification failed!")
            
        await conn.close()
        print("🎉 Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(apply_migration())