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
import subprocess
from urllib.parse import urlparse, urlunparse

logger = logging.getLogger(__name__)

def get_cloud_sql_ip(instance_name: str, project_id: str = None) -> Optional[str]:
    """
    Get the private IP address of a Cloud SQL instance using gcloud commands.
    
    Args:
        instance_name: Name of the Cloud SQL instance
        project_id: GCP project ID (optional, uses default if not provided)
    
    Returns:
        Private IP address of the instance or None if not found
    """
    try:
        # Build gcloud command
        cmd = ['gcloud', 'sql', 'instances', 'describe', instance_name]
        if project_id:
            cmd.extend(['--project', project_id])
        cmd.extend(['--format', 'value(ipAddresses[0].ipAddress)'])
        
        # Execute command
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            ip = result.stdout.strip()
            logger.info(f"Resolved Cloud SQL instance {instance_name} to IP: {ip}")
            return ip
        else:
            logger.warning(f"Could not resolve Cloud SQL instance {instance_name}: {result.stderr}")
            return None
            
    except Exception as e:
        logger.warning(f"Error resolving Cloud SQL IP for {instance_name}: {e}")
        return None

def resolve_database_url(database_url: str) -> str:
    """
    Resolve database URL by replacing hostname with Cloud SQL internal IP and correct credentials.
    
    Args:
        database_url: Original database URL
        
    Returns:
        Resolved database URL with correct IP and credentials
    """
    try:
        parsed = urlparse(database_url)
        
        # Known Cloud SQL configuration
        CLOUD_SQL_INTERNAL_IP = "10.92.0.3"
        CLOUD_SQL_USERNAME = "arccorp_sys_admin"
        
        # If hostname looks like a Cloud SQL instance name or non-IP, use the known internal IP
        if parsed.hostname and not _is_ip_address(parsed.hostname):
            logger.info(f"Resolving hostname {parsed.hostname} to Cloud SQL internal IP {CLOUD_SQL_INTERNAL_IP}")
            
            # Get password from Google Secrets Manager
            try:
                password = _get_db_password_from_secrets()
            except Exception as e:
                logger.warning(f"Could not get password from secrets, using original: {e}")
                password = parsed.password
            
            # Replace hostname and credentials with known values
            netloc = f"{CLOUD_SQL_USERNAME}:{password}@{CLOUD_SQL_INTERNAL_IP}"
            if parsed.port:
                netloc += f":{parsed.port}"
                
            resolved_url = urlunparse((
                parsed.scheme,
                netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            
            logger.info("Resolved database URL using Cloud SQL internal IP and credentials")
            return resolved_url
        
        # If hostname is already an IP or localhost, return as-is
        return database_url
        
    except Exception as e:
        logger.warning(f"Error resolving database URL: {e}")
        return database_url

def _get_db_password_from_secrets() -> str:
    """Get database password from Google Secrets Manager."""
    try:
        from google.cloud import secretmanager
        
        # Initialize the client
        client = secretmanager.SecretManagerServiceClient()
        
        # Get project ID from environment or use default
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'rl-prod-471116')
        
        # Try different possible secret names for the database password
        secret_names = ["database-password", "DATABASE_PASSWORD", "db-password"]
        
        for secret_name in secret_names:
            try:
                name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
                response = client.access_secret_version(request={"name": name})
                return response.payload.data.decode("UTF-8")
            except Exception:
                continue
        
        raise Exception("No database password secret found")
        
    except Exception as e:
        logger.error(f"Error getting database password from secrets: {e}")
        raise

def _is_ip_address(hostname: str) -> bool:
    """Check if hostname is already an IP address."""
    try:
        parts = hostname.split('.')
        if len(parts) == 4:
            return all(0 <= int(part) <= 255 for part in parts)
    except (ValueError, AttributeError):
        pass
    return hostname in ['localhost', '127.0.0.1']

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
        # Resolve the database URL to get the correct IP
        self.database_url = resolve_database_url(database_url)
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
