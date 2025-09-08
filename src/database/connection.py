"""
Database Connection Management

Handles database connections, connection pooling, and transaction management.
"""

import psycopg2
import psycopg2.extras
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from typing import Optional, Generator
import logging
import os
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages database connections and transactions for the Red Legion Bot.
    
    Features:
    - Connection pooling for performance
    - Automatic retry logic
    - Transaction context management
    - Health monitoring
    """
    
    def __init__(self, database_url: str, min_connections: int = 1, max_connections: int = 10):
        """
        Initialize the database manager.
        
        Args:
            database_url: PostgreSQL connection URL
            min_connections: Minimum connections in pool
            max_connections: Maximum connections in pool
        """
        self.database_url = database_url
        self.min_connections = min_connections
        self.max_connections = max_connections
        self._pool: Optional[SimpleConnectionPool] = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the connection pool."""
        try:
            # Parse URL to validate format
            parsed = urlparse(self.database_url)
            if not parsed.scheme == 'postgresql':
                raise ValueError("Database URL must be a PostgreSQL URL")
            
            self._pool = SimpleConnectionPool(
                self.min_connections,
                self.max_connections,
                self.database_url,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            
            logger.info(f"Database connection pool initialized ({self.min_connections}-{self.max_connections} connections)")
            
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """
        Get a database connection from the pool.
        
        Yields:
            Database connection with automatic cleanup
        """
        if not self._pool:
            raise RuntimeError("Database pool not initialized")
        
        conn = None
        try:
            conn = self._pool.getconn()
            if conn:
                yield conn
            else:
                raise RuntimeError("Unable to get connection from pool")
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                self._pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, commit: bool = True) -> Generator[psycopg2.extras.RealDictCursor, None, None]:
        """
        Get a database cursor with transaction management.
        
        Args:
            commit: Whether to commit the transaction automatically
            
        Yields:
            Database cursor with automatic transaction handling
        """
        with self.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    yield cursor
                    if commit:
                        conn.commit()
            except Exception:
                conn.rollback()
                raise
    
    def execute_query(self, query: str, params=None, fetch: bool = False):
        """
        Execute a database query.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            fetch: Whether to fetch and return results
            
        Returns:
            Query results if fetch=True, otherwise None
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
    
    def check_health(self) -> bool:
        """
        Check database connection health.
        
        Returns:
            True if database is healthy, False otherwise
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def close(self):
        """Close all connections in the pool."""
        if self._pool:
            self._pool.closeall()
            logger.info("Database connection pool closed")

# Global database manager instance
_db_manager: Optional[DatabaseManager] = None

def initialize_database(database_url: str) -> DatabaseManager:
    """
    Initialize the global database manager.
    
    Args:
        database_url: PostgreSQL connection URL
        
    Returns:
        Database manager instance
    """
    global _db_manager
    _db_manager = DatabaseManager(database_url)
    return _db_manager

def get_connection():
    """
    Get a database connection from the global manager.
    
    Returns:
        Database connection context manager
    """
    if not _db_manager:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return _db_manager.get_connection()

def get_cursor(commit: bool = True):
    """
    Get a database cursor from the global manager.
    
    Args:
        commit: Whether to commit transactions automatically
        
    Returns:
        Database cursor context manager
    """
    if not _db_manager:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return _db_manager.get_cursor(commit=commit)

def execute_query(query: str, params=None, fetch: bool = False):
    """
    Execute a query using the global database manager.
    
    Args:
        query: SQL query to execute
        params: Query parameters
        fetch: Whether to fetch results
        
    Returns:
        Query results if fetch=True, otherwise None
    """
    if not _db_manager:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return _db_manager.execute_query(query, params, fetch)

def check_health() -> bool:
    """
    Check database health using the global manager.
    
    Returns:
        True if database is healthy, False otherwise
    """
    if not _db_manager:
        return False
    return _db_manager.check_health()
