"""
Database Schema Initialization

Handles database schema creation and management.
"""

from typing import List
import logging
from ..connection import get_cursor
from .core import COMPLETE_SCHEMA, SCHEMA_VERSION, SCHEMA_DESCRIPTION

logger = logging.getLogger(__name__)

class SchemaManager:
    """Manages database schema operations."""
    
    @staticmethod
    def initialize_schema() -> bool:
        """
        Initialize the complete database schema.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Initializing database schema: {SCHEMA_DESCRIPTION}")
            logger.info(f"Schema version: {SCHEMA_VERSION}")
            
            with get_cursor() as cursor:
                # Execute each schema section
                for i, schema_section in enumerate(COMPLETE_SCHEMA, 1):
                    logger.info(f"Executing schema section {i}/{len(COMPLETE_SCHEMA)}")
                    cursor.execute(schema_section)
                
                # Create schema version tracking table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_metadata (
                        version VARCHAR(20) PRIMARY KEY,
                        description TEXT,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Record this schema version
                cursor.execute("""
                    INSERT INTO schema_metadata (version, description)
                    VALUES (%s, %s)
                    ON CONFLICT (version) DO UPDATE SET
                        description = EXCLUDED.description,
                        applied_at = CURRENT_TIMESTAMP
                """, (SCHEMA_VERSION, SCHEMA_DESCRIPTION))
                
            logger.info("Database schema initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")
            return False
    
    @staticmethod
    def check_schema_version() -> str:
        """
        Check the current schema version.
        
        Returns:
            Current schema version or 'unknown' if not found
        """
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT version FROM schema_metadata 
                    ORDER BY applied_at DESC 
                    LIMIT 1
                """)
                result = cursor.fetchone()
                return result['version'] if result else 'unknown'
        except Exception:
            return 'unknown'
    
    @staticmethod
    def validate_schema() -> bool:
        """
        Validate that all required tables exist.
        
        Returns:
            True if schema is valid, False otherwise
        """
        required_tables = [
            'guilds',
            'users', 
            'guild_memberships',
            'mining_events',
            'mining_channels',
            'mining_participation',
            'materials',
            'mining_yields',
            'loans',
            'schema_metadata'
        ]
        
        try:
            with get_cursor() as cursor:
                for table in required_tables:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = %s
                        )
                    """, (table,))
                    
                    exists = cursor.fetchone()['exists']
                    if not exists:
                        logger.error(f"Required table '{table}' not found")
                        return False
                
            logger.info("Schema validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return False
    
    @staticmethod
    def get_table_info() -> dict:
        """
        Get information about all tables in the database.
        
        Returns:
            Dictionary with table information
        """
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        table_name,
                        (SELECT COUNT(*) FROM information_schema.columns 
                         WHERE table_name = t.table_name AND table_schema = 'public') as column_count
                    FROM information_schema.tables t
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
                
                tables = cursor.fetchall()
                return {row['table_name']: row['column_count'] for row in tables}
                
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return {}

def init_database(database_url=None) -> bool:
    """
    Initialize the database with the complete schema.
    
    Args:
        database_url (str, optional): Database URL (ignored for compatibility)
    
    Returns:
        True if successful, False otherwise
    """
    schema_manager = SchemaManager()
    
    # Initialize schema
    if not schema_manager.initialize_schema():
        return False
    
    # Validate schema
    if not schema_manager.validate_schema():
        return False
    
    logger.info("Database initialization completed successfully")
    return True
