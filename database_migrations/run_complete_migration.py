#!/usr/bin/env python3
"""
Complete Database Migration Runner for Red Legion Bot
Executes all migration files in order to support new subcommand systems

Migration Order:
1. 01_market_system.sql - Market/trading functionality
2. 02_enhanced_loan_system.sql - Comprehensive loan system with workflows
3. 03_application_system.sql - Organization recruitment and application system
4. 04_system_tables.sql - Analytics, monitoring, and administrative features

This script safely executes all migrations with proper error handling and rollback support.
"""

import asyncio
import asyncpg
import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Migration files in execution order
MIGRATION_FILES = [
    "00_foundation_schema.sql",
    "01_market_system.sql",
    "02_enhanced_loan_system.sql", 
    "03_application_system.sql",
    "04_system_tables.sql"
]

async def get_database_url():
    """Get database URL from config or environment"""
    try:
        # Try to read from db_url.txt first
        db_url_file = Path(__file__).parent.parent / "db_url.txt"
        if db_url_file.exists():
            with open(db_url_file, 'r') as f:
                return f.read().strip()
    except Exception as e:
        logger.warning(f"Could not read db_url.txt: {e}")
    
    # Try environment variable
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        return db_url
    
    # Try local config
    try:
        sys.path.append(str(Path(__file__).parent.parent / "src"))
        from config import DATABASE_URL
        return DATABASE_URL
    except ImportError:
        logger.error("Could not import DATABASE_URL from config")
    
    raise ValueError("No database URL found. Set DATABASE_URL environment variable or create db_url.txt")

async def execute_migration_file(connection, file_path: Path):
    """Execute a single migration file"""
    logger.info(f"Executing migration: {file_path.name}")
    
    try:
        with open(file_path, 'r') as f:
            sql_content = f.read()
        
        if not sql_content.strip():
            logger.warning(f"Migration file {file_path.name} is empty, skipping")
            return True
        
        # Execute the migration
        await connection.execute(sql_content)
        logger.info(f"✅ Successfully executed {file_path.name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to execute {file_path.name}: {e}")
        return False

async def create_migration_log_table(connection):
    """Create table to track migration execution"""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS migration_log (
        migration_id SERIAL PRIMARY KEY,
        filename VARCHAR(100) NOT NULL,
        executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        success BOOLEAN NOT NULL,
        error_message TEXT,
        execution_time_ms INTEGER
    );
    
    CREATE INDEX IF NOT EXISTS idx_migration_log_filename ON migration_log(filename);
    CREATE INDEX IF NOT EXISTS idx_migration_log_executed ON migration_log(executed_at);
    """
    
    await connection.execute(create_table_sql)
    logger.info("Migration log table created/verified")

async def log_migration_execution(connection, filename: str, success: bool, execution_time_ms: int, error_message: str = None):
    """Log migration execution to database"""
    await connection.execute(
        """
        INSERT INTO migration_log (filename, success, execution_time_ms, error_message)
        VALUES ($1, $2, $3, $4)
        """,
        filename, success, execution_time_ms, error_message
    )

async def check_migration_executed(connection, filename: str) -> bool:
    """Check if migration was already successfully executed"""
    result = await connection.fetchval(
        "SELECT EXISTS(SELECT 1 FROM migration_log WHERE filename = $1 AND success = true)",
        filename
    )
    return result

async def run_migrations():
    """Main migration execution function"""
    logger.info("🚀 Starting Red Legion Bot Database Migration")
    logger.info("=" * 60)
    
    try:
        # Get database URL
        database_url = await get_database_url()
        logger.info(f"Connecting to database: {database_url.split('@')[1] if '@' in database_url else 'local'}")
        
        # Connect to database
        connection = await asyncpg.connect(database_url)
        logger.info("✅ Database connection established")
        
        # Create migration log table
        await create_migration_log_table(connection)
        
        # Get script directory
        script_dir = Path(__file__).parent
        
        # Execute migrations in order
        successful_migrations = 0
        failed_migrations = 0
        
        for migration_file in MIGRATION_FILES:
            file_path = script_dir / migration_file
            
            if not file_path.exists():
                logger.error(f"❌ Migration file not found: {migration_file}")
                failed_migrations += 1
                continue
            
            # Check if already executed
            if await check_migration_executed(connection, migration_file):
                logger.info(f"⏭️  Skipping {migration_file} (already executed successfully)")
                continue
            
            # Execute migration with timing
            start_time = datetime.now()
            success = await execute_migration_file(connection, file_path)
            end_time = datetime.now()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Log the execution
            error_message = None if success else f"Migration failed during execution"
            await log_migration_execution(
                connection, migration_file, success, execution_time_ms, error_message
            )
            
            if success:
                successful_migrations += 1
            else:
                failed_migrations += 1
                logger.error(f"Migration {migration_file} failed - stopping execution")
                break
        
        # Close connection
        await connection.close()
        
        # Print summary
        logger.info("=" * 60)
        logger.info("🏁 Migration Summary:")
        logger.info(f"   ✅ Successful: {successful_migrations}")
        logger.info(f"   ❌ Failed: {failed_migrations}")
        logger.info(f"   📊 Total: {successful_migrations + failed_migrations}")
        
        if failed_migrations == 0:
            logger.info("🎉 All migrations completed successfully!")
            logger.info("Your Red Legion Bot database is ready for the new subcommand systems:")
            logger.info("   • /red-events (Event management)")
            logger.info("   • /red-market (Trading system)")
            logger.info("   • /red-loans (Loan management with workflows)")
            logger.info("   • /red-join (Organization recruitment)")
            return True
        else:
            logger.error("💥 Some migrations failed. Please check the logs and fix any issues.")
            return False
            
    except Exception as e:
        logger.error(f"💥 Migration process failed: {e}")
        return False

async def verify_migration_integrity():
    """Verify that all expected tables and structures exist"""
    logger.info("🔍 Verifying migration integrity...")
    
    try:
        database_url = await get_database_url()
        connection = await asyncpg.connect(database_url)
        
        # Expected tables from each migration
        expected_tables = {
            "00_foundation_schema.sql": [
                "users", "guilds", "guild_memberships", "mining_channels",
                "mining_events", "events", "mining_participation", "loans",
                "materials", "mining_yields", "command_usage", "adhoc_sessions"
            ],
            "01_market_system.sql": [
                "market_listings", "market_categories", "market_transactions", 
                "market_settings", "market_favorites", "market_reputation"
            ],
            "02_enhanced_loan_system.sql": [
                "loan_payments", "loan_reminders", "loan_settings"
            ],
            "03_application_system.sql": [
                "applications", "application_reviews", "application_positions",
                "application_settings", "application_notifications"
            ],
            "04_system_tables.sql": [
                "user_activity", "system_notifications", "bot_config",
                "user_preferences", "audit_log", "system_metrics",
                "error_logs", "feature_analytics", "scheduled_tasks"
            ]
        }
        
        missing_tables = []
        for migration, tables in expected_tables.items():
            for table in tables:
                exists = await connection.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = $1)",
                    table
                )
                if not exists:
                    missing_tables.append(f"{table} (from {migration})")
        
        await connection.close()
        
        if missing_tables:
            logger.warning(f"⚠️  Missing tables: {', '.join(missing_tables)}")
            return False
        else:
            logger.info("✅ All expected tables are present")
            return True
            
    except Exception as e:
        logger.error(f"❌ Integrity verification failed: {e}")
        return False

if __name__ == "__main__":
    print("Red Legion Bot - Database Migration Tool")
    print("=======================================")
    
    # Run migrations
    success = asyncio.run(run_migrations())
    
    if success:
        # Verify integrity
        asyncio.run(verify_migration_integrity())
        print("\n🎯 Next Steps:")
        print("1. Update your bot's main.py to load the new subcommand modules")
        print("2. Test the new commands in your Discord server")
        print("3. Configure any guild-specific settings using the bot commands")
        print("4. Monitor the logs for any issues")
    else:
        print("\n❌ Migration failed. Please check the logs and try again.")
        sys.exit(1)