"""
Database initialization helper for deployment compatibility.

This module provides a simple interface for database initialization that works
with both the new architecture and legacy deployment scripts.
"""

import os
import logging
from database import DatabaseManager
from database.connection import initialize_database
from database.schemas import init_database as schema_init
from config.settings import get_database_url

logger = logging.getLogger(__name__)

def init_database_for_deployment(db_url=None):
    """
    Initialize database for deployment.
    
    This function handles both new architecture initialization and legacy compatibility.
    Returns True if successful, False otherwise.
    
    Args:
        db_url (str, optional): Database URL. If not provided, gets from config.
    """
    try:
        # Get database URL
        if db_url is None:
            db_url = get_database_url()
        if not db_url:
            logger.error("No database URL configured")
            return False
        
        logger.info("Initializing database for deployment...")
        
        # Initialize the global database manager first
        db_manager = initialize_database(db_url)
        logger.info("Global database manager initialized")
        
        # Initialize schema using the existing manager (don't pass URL to avoid double initialization)
        if schema_init():
            logger.info("✅ Database schema initialized successfully")
            return True
        else:
            logger.error("❌ Database schema initialization failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False

# Legacy compatibility
def init_database(db_url=None):
    """Legacy function for backward compatibility."""
    if db_url:
        # Legacy call with URL - ignore the URL and use config
        return init_database_for_deployment()
    else:
        # New call without URL
        return init_database_for_deployment()

# Export both functions
__all__ = ['init_database_for_deployment', 'init_database']
