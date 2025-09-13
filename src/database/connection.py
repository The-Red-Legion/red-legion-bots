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
    Resolve database URL by using the complete connection string from Secret Manager if available.
    
    Args:
        database_url: Original database URL
        
    Returns:
        Resolved database URL with correct IP and credentials
    """
    try:
        logger.info("Processing database URL for connection resolution...")
        parsed = urlparse(database_url)
        logger.info(f"Parsed hostname: {parsed.hostname or '[redacted]'}, port: {parsed.port or '[default]'}, username: {parsed.username or '[redacted]'}")
        
        # If the URL already has the correct Cloud SQL IP, use it as-is
        if parsed.hostname == "10.92.0.3":
            logger.info("Database URL already using Cloud SQL internal IP, returning as-is")
            return database_url
        
        # If hostname is localhost or other IP, return as-is
        if _is_ip_address(parsed.hostname) or parsed.hostname in ['localhost']:
            logger.info("Database URL using localhost/IP address, returning as-is")
            return database_url
            
        # If hostname looks like a Cloud SQL instance name, try to get the complete URL from secrets
        if parsed.hostname and not _is_ip_address(parsed.hostname):
            logger.info(f"Hostname {parsed.hostname} appears to be Cloud SQL instance, getting complete URL from Secret Manager")
            
            try:
                # Try to get the complete connection string from Secret Manager
                from google.cloud import secretmanager
                import os
                
                client = secretmanager.SecretManagerServiceClient()
                project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'rl-prod-471116')
                secret_name = "database-connection-string"
                name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
                
                response = client.access_secret_version(request={"name": name})
                complete_url = response.payload.data.decode("UTF-8")
                
                # Validate the complete URL has the correct format
                complete_parsed = urlparse(complete_url)
                if complete_parsed.scheme == 'postgresql' and complete_parsed.hostname == "10.92.0.3":
                    logger.info("Successfully retrieved complete database URL from Secret Manager")
                    return complete_url
                else:
                    logger.warning("Complete URL from Secret Manager has unexpected format, falling back to manual construction")
                    
            except Exception as e:
                logger.warning(f"Could not get complete URL from Secret Manager: {e}")
            
            # Fallback to manual construction (legacy behavior)
            logger.info("Falling back to manual URL construction")
            CLOUD_SQL_INTERNAL_IP = "10.92.0.3"
            CLOUD_SQL_USERNAME = "arccorp_sys_admin"
            
            # Get password from Google Secrets Manager
            try:
                password = _get_db_password_from_secrets()
                logger.info("Successfully retrieved password from Google Secrets Manager")
            except Exception as e:
                logger.warning(f"Could not get password from secrets, using original: {e}")
                password = parsed.password if parsed.password else "fallback_password"
            
            # Use original port or default to 5432
            port = parsed.port if parsed.port else 5432
            
            # URL-encode the password to handle special characters
            from urllib.parse import quote
            encoded_password = quote(password, safe='')
            
            # Get database name from the path, default to the production database
            database_name = parsed.path.lstrip('/') if parsed.path else 'red_legion_arccorp_data_store'
            resolved_url = f"postgresql://{CLOUD_SQL_USERNAME}:{encoded_password}@{CLOUD_SQL_INTERNAL_IP}:{port}/{database_name}"
            
            logger.info(f"Manually constructed URL: postgresql://{CLOUD_SQL_USERNAME}:***@{CLOUD_SQL_INTERNAL_IP}:{port}/{database_name}")
            return resolved_url
        
        # Default case: return as-is
        logger.info("No special handling needed, returning original URL")
        return database_url
        
    except Exception as e:
        logger.error(f"Error resolving database URL: {e}")
        logger.error("Failed to resolve database URL - check connection parameters")
        # Return a safe fallback URL
        try:
            # Try to get complete URL from secrets first
            from google.cloud import secretmanager
            import os
            
            client = secretmanager.SecretManagerServiceClient()
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'rl-prod-471116')
            secret_name = "database-connection-string"
            name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
            
            response = client.access_secret_version(request={"name": name})
            fallback_url = response.payload.data.decode("UTF-8")
            logger.info("Using complete fallback URL from Secret Manager")
            return fallback_url
        except:
            # Ultimate fallback - construct manually
            try:
                password = _get_db_password_from_secrets()
                from urllib.parse import quote
                encoded_password = quote(password, safe='')
                fallback_url = f"postgresql://arccorp_sys_admin:{encoded_password}@10.92.0.3:5432/red_legion_arccorp_data_store"
                logger.info("Using manually constructed fallback URL")
                return fallback_url
            except:
                logger.error("Could not create fallback URL, returning original")
                return database_url

def _get_db_password_from_secrets() -> str:
    """Get database password from Google Secrets Manager."""
    try:
        from google.cloud import secretmanager
        
        # Initialize the client
        client = secretmanager.SecretManagerServiceClient()
        
        # Get project ID from environment or use default
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'rl-prod-471116')
        
        # Use the correct secret name for database password
        secret_name = "db-password"
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        
        # Access the secret version
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
        
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
            # Parse URL to validate format (log safely without credentials)
            parsed = urlparse(self.database_url)
            logger.info("Initializing database connection pool...")
            logger.info(f"Database - scheme: {parsed.scheme}, hostname: {parsed.hostname or '[redacted]'}, port: {parsed.port or '[default]'}")
            
            if not parsed.scheme == 'postgresql':
                raise ValueError("Database URL must be a PostgreSQL URL")
            
            # Test connection first to provide better error messages
            logger.info("Testing database connection...")
            test_conn = psycopg2.connect(self.database_url)
            test_conn.close()
            logger.info("Database connection test successful")
            
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
                # Handle RealDictRow (dictionary-like) result
                if hasattr(result, 'values'):
                    return list(result.values())[0] == 1
                else:
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
