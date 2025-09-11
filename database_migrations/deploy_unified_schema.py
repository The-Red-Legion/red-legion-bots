#!/usr/bin/env python3
"""
Robust Unified Schema Migration for Red Legion Bot v2.0

This script deploys the unified event-centric database schema.
It includes better error handling and doesn't rely on the health check method.
"""

import sys
import os
import logging
import json
from pathlib import Path

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

def run_migration():
    """Run the unified database migration with robust error handling."""
    logger = setup_logging()
    
    try:
        logger.info("🚀 Starting unified database migration for Red Legion Bot v2.0")
        
        # Add src to path for imports
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        src_path = project_root / 'src'
        sys.path.insert(0, str(src_path))
        
        logger.info(f"📁 Project paths - Root: {project_root}, Src: {src_path}")
        
        # Import database components
        try:
            from config.settings import get_database_url
            logger.info("✅ Imported config.settings")
        except Exception as e:
            raise ImportError(f"Failed to import config.settings: {e}")
        
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            logger.info("✅ Imported psycopg2")
        except Exception as e:
            raise ImportError(f"Failed to import psycopg2: {e}")
        
        # Get database URL
        database_url = get_database_url()
        if not database_url:
            raise ValueError("Database URL not found - check configuration")
        
        logger.info("🔗 Database connection configured")
        
        # Test direct database connection (bypassing health check)
        logger.info("🔍 Testing database connection...")
        
        try:
            conn = psycopg2.connect(database_url)
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                if result['test'] != 1:
                    raise RuntimeError("Database connection test failed")
            conn.close()
            logger.info("✅ Database connection test successful")
        except Exception as e:
            raise RuntimeError(f"Database connection failed: {e}")
        
        # Read migration file
        migration_file = script_dir / '10_unified_mining_system.sql'
        
        if not migration_file.exists():
            raise FileNotFoundError(f"Migration file not found: {migration_file}")
        
        logger.info(f"📖 Reading migration file: {migration_file}")
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        logger.info(f"📝 Migration SQL loaded ({len(migration_sql)} characters)")
        
        # Check if migration already applied
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        
        logger.info("🔍 Checking if migration already applied...")
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT migration_name, applied_at, success 
                    FROM schema_migrations 
                    WHERE migration_name = '10_unified_mining_system.sql' 
                    AND success = true
                """)
                existing_migration = cursor.fetchone()
                
                if existing_migration:
                    logger.info(f"✅ Migration already applied successfully at {existing_migration['applied_at']}")
                    logger.info("🚀 Skipping migration execution - unified schema already exists")
                    
                    # Verify tables still exist
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name IN ('events', 'participation', 'payrolls', 'uex_prices')
                        ORDER BY table_name
                    """)
                    tables = [row['table_name'] for row in cursor.fetchall()]
                    
                    conn.close()
                    
                    # Return success status
                    result = {
                        'status': 'success',
                        'message': 'Migration already applied - unified schema verified',
                        'migration_file': '10_unified_mining_system.sql',
                        'tables_created': tables,
                        'timestamp': existing_migration['applied_at'].isoformat() if existing_migration['applied_at'] else None
                    }
                    
                    logger.info("🎉 Migration verification completed successfully!")
                    print(json.dumps(result))
                    return 0
        except Exception as e:
            logger.info(f"Schema migrations table not found or error checking: {e}")
            logger.info("Proceeding with fresh migration...")
        
        # Execute migration
        logger.info("⚠️  Executing unified mining system migration...")
        logger.info("⚠️  This will DROP all existing mining-related tables!")
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Execute migration in chunks if needed
                logger.info("🔄 Executing migration SQL...")
                cursor.execute(migration_sql)
                logger.info("✅ Migration SQL executed successfully")
                
        except Exception as e:
            logger.error(f"❌ Migration execution failed: {e}")
            conn.close()
            raise
        
        # Verify migration results
        logger.info("🔍 Verifying migration results...")
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
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
            
            logger.info(f"✅ Migration verification successful - found tables: {tables}")
            
            # Check migration record
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT migration_name, applied_at, success 
                    FROM schema_migrations 
                    WHERE migration_name = '10_unified_mining_system.sql'
                """)
                result = cursor.fetchone()
            
            if not result or not result['success']:
                logger.warning("⚠️  Migration record not found or marked as failed, but tables exist")
            else:
                logger.info(f"✅ Migration record verified: {result['migration_name']} applied at {result['applied_at']}")
        
        except Exception as e:
            logger.error(f"❌ Migration verification failed: {e}")
            conn.close()
            raise
        
        finally:
            conn.close()
        
        # Return success status
        result = {
            'status': 'success',
            'message': 'Unified database migration completed successfully',
            'migration_file': '10_unified_mining_system.sql',
            'tables_created': tables,
            'timestamp': None
        }
        
        logger.info("🎉 Migration completed successfully!")
        print(json.dumps(result))
        return 0
        
    except Exception as e:
        logger.error(f"💥 Migration failed: {e}")
        
        # Return error status
        error_result = {
            'status': 'error',
            'message': str(e),
            'migration_file': '10_unified_mining_system.sql'
        }
        
        print(json.dumps(error_result))
        return 1

if __name__ == '__main__':
    sys.exit(run_migration())