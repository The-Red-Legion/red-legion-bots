#!/usr/bin/env python3
"""
Event Scheduling and Real-time Monitoring Migration Runner

Applies migration 17_event_scheduling_and_monitoring.sql to add:
- Event scheduling capabilities
- Real-time participant tracking
- Live monitoring dashboard support
"""

import sys
import os
import logging
import asyncpg
from pathlib import Path

# Add src directory to path for imports
script_dir = Path(__file__).parent
project_root = script_dir.parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

def setup_logging():
    """Configure logging for migration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment or config."""
    try:
        from config.settings import get_database_url
        return get_database_url()
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Could not get database URL from config: {e}")
        
        # Fallback to environment variable
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            logger.info("Using DATABASE_URL environment variable")
            return db_url
            
        logger.error("No database URL available. Set DATABASE_URL environment variable or configure in settings.")
        return None

async def run_migration():
    """Run the event scheduling and monitoring migration."""
    logger = setup_logging()
    
    try:
        logger.info("Starting Event Scheduling and Real-time Monitoring Migration (17)")
        
        # Get database connection
        database_url = get_database_url()
        if not database_url:
            logger.error("❌ No database URL available")
            return False
        
        logger.info(f"📡 Connecting to database...")
        
        # Read migration file
        migration_file = Path(__file__).parent / "17_event_scheduling_and_monitoring.sql"
        if not migration_file.exists():
            logger.error(f"❌ Migration file not found: {migration_file}")
            return False
            
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Connect and execute migration
        conn = await asyncpg.connect(database_url)
        
        try:
            logger.info("🔄 Executing migration SQL...")
            await conn.execute(migration_sql)
            
            # Verify the migration worked by checking new tables
            logger.info("✅ Verifying migration results...")
            
            # Check new columns in events table
            result = await conn.fetch("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'events' 
                  AND column_name IN ('scheduled_start_time', 'auto_start_enabled', 'tracked_channels', 'event_status')
            """)
            
            new_columns = [row['column_name'] for row in result]
            logger.info(f"✅ New events columns: {new_columns}")
            
            # Check new tables
            result = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name IN ('event_participant_snapshots', 'scheduled_event_queue', 'event_metrics')
                  AND table_schema = 'public'
            """)
            
            new_tables = [row['table_name'] for row in result]
            logger.info(f"✅ New tables created: {new_tables}")
            
            # Check functions
            result = await conn.fetch("""
                SELECT routine_name 
                FROM information_schema.routines 
                WHERE routine_name IN ('update_participation_duration', 'create_participant_snapshot')
                  AND routine_schema = 'public'
            """)
            
            new_functions = [row['routine_name'] for row in result]
            logger.info(f"✅ New functions created: {new_functions}")
            
            logger.info("🎉 Migration 17 completed successfully!")
            return True
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        return False

async def main():
    """Main entry point."""
    success = await run_migration()
    if success:
        print("\n🎉 Event Scheduling and Monitoring Migration completed successfully!")
        print("✅ Database schema updated with:")
        print("   • Event scheduling fields")
        print("   • Real-time participant tracking")
        print("   • Live monitoring support tables")
        print("   • Helper functions for real-time updates")
        return 0
    else:
        print("\n❌ Migration failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)