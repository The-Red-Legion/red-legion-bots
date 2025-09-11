#!/usr/bin/env python3
"""
Unified Database Migration Runner for Red Legion Bot v2.0

Applies the complete unified mining system schema migration.
This script drops all legacy tables and creates the new event-centric schema.

WARNING: This is a destructive migration that removes all existing data.
Only run this on development systems or for complete fresh deployment.
"""

import sys
import os
import logging
import json
from pathlib import Path

# Add src directory to path for imports
# Navigate from database_migrations/ to src/
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
    from config.settings import get_database_url
    return get_database_url()

def run_migration():
    """Run the unified database migration."""
    logger = setup_logging()
    
    try:
        logger.info("Starting unified database migration for Red Legion Bot v2.0")
        
        # Get database connection
        database_url = get_database_url()
        if not database_url:
            raise ValueError("Database URL not found - check configuration")
        
        logger.info("Database connection configured")
        
        # Import database operations
        from database.connection import DatabaseManager
        
        # Initialize database manager
        db_manager = DatabaseManager(database_url)
        
        # Test connection
        if not db_manager.check_health():
            raise RuntimeError("Database health check failed")
        
        logger.info("Database connection verified")
        
        # Read migration file
        migration_file = Path(__file__).parent / '10_unified_mining_system.sql'
        
        if not migration_file.exists():
            raise FileNotFoundError(f"Migration file not found: {migration_file}")
        
        logger.info(f"Reading migration file: {migration_file}")
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        logger.info("Executing unified mining system migration...")
        logger.warning("This will DROP all existing mining-related tables!")
        
        with db_manager.get_cursor() as cursor:
            cursor.execute(migration_sql)
        
        logger.info("Migration executed successfully")
        
        # Verify migration
        logger.info("Verifying migration results...")
        
        with db_manager.get_cursor() as cursor:
            # Check that key tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('events', 'participation', 'payrolls', 'uex_prices')
                ORDER BY table_name
            """)
            tables = [row['table_name'] for row in cursor.fetchall()]
        
        expected_tables = ['events', 'participation', 'payrolls', 'uex_prices']
        missing_tables = set(expected_tables) - set(tables)
        
        if missing_tables:
            raise RuntimeError(f"Migration verification failed - missing tables: {missing_tables}")
        
        logger.info(f"Migration verification successful - found tables: {tables}")
        
        # Check migration record
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT migration_name, applied_at, success 
                FROM schema_migrations 
                WHERE migration_name = '10_unified_mining_system.sql'
            """)
            result = cursor.fetchone()
        
        if not result or not result['success']:
            raise RuntimeError("Migration record not found or marked as failed")
        
        logger.info(f"Migration record verified: {result['migration_name']} applied at {result['applied_at']}")
        
        # Return success status for Ansible
        result = {
            'status': 'success',
            'message': 'Unified database migration completed successfully',
            'migration_file': '10_unified_mining_system.sql',
            'tables_created': tables,
            'applied_at': result['applied_at'].isoformat() if result['applied_at'] else None
        }
        
        print(json.dumps(result))
        return 0
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        
        # Return error status for Ansible
        error_result = {
            'status': 'error',
            'message': str(e),
            'migration_file': '10_unified_mining_system.sql'
        }
        
        print(json.dumps(error_result))
        return 1

if __name__ == '__main__':
    sys.exit(run_migration())