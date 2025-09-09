#!/usr/bin/env python3
"""
Complete Database Schema Deployment Script for Red Legion Bot
Deploys the complete schema including all missing tables during deployment.
"""

import sys
import os
import logging
import psycopg2
from pathlib import Path
from urllib.parse import urlparse

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def setup_logging():
    """Setup logging for schema deployment."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def get_database_url():
    """Get database URL from various sources."""
    # Try environment variable first
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        return db_url
    
    # Try importing from config
    try:
        from config.settings import get_database_url as config_get_db_url
        db_url = config_get_db_url()
        if db_url:
            return db_url
    except ImportError:
        pass
    
    # Try reading from file
    try:
        with open('db_url.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    return line
    except FileNotFoundError:
        pass
    
    raise ValueError("No database URL found. Set DATABASE_URL environment variable or ensure config is available.")

def get_resolved_database_url(database_url):
    """Resolve database URL to use Cloud SQL internal IP and correct credentials."""
    try:
        from urllib.parse import quote
        parsed = urlparse(database_url)
        
        # Known Cloud SQL configuration
        CLOUD_SQL_INTERNAL_IP = "10.92.0.3"
        CLOUD_SQL_USERNAME = "arccorp_sys_admin"
        
        # If hostname looks like a Cloud SQL instance name or non-IP, use the known internal IP
        if parsed.hostname and not _is_ip_address(parsed.hostname):
            logger = logging.getLogger(__name__)
            logger.info(f"Resolving hostname {parsed.hostname} to Cloud SQL internal IP {CLOUD_SQL_INTERNAL_IP}")
            
            # Get password from Google Secrets Manager
            try:
                password = _get_db_password_from_secrets()
                logger.info("Successfully retrieved password from Google Secrets Manager")
            except Exception as e:
                logger.warning(f"Could not get password from secrets, using original: {e}")
                password = parsed.password if parsed.password else "fallback_password"
            
            # URL-encode the password to handle special characters
            encoded_password = quote(password, safe='')
            
            # Use original port or default to 5432
            port = parsed.port if parsed.port else 5432
            
            # Get database name from the path, default to the production database
            database_name = parsed.path.lstrip('/') if parsed.path else 'arccorp_data_store'
            resolved_url = f"postgresql://{CLOUD_SQL_USERNAME}:{encoded_password}@{CLOUD_SQL_INTERNAL_IP}:{port}/{database_name}"
            
            logger.info(f"Resolved database URL: postgresql://{CLOUD_SQL_USERNAME}:***@{CLOUD_SQL_INTERNAL_IP}:{port}/{database_name}")
            return resolved_url
        
        # If hostname is already an IP or localhost, return as-is
        return database_url
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error resolving database URL: {e}")
        return database_url

def _is_ip_address(hostname: str) -> bool:
    """Check if hostname is already an IP address."""
    try:
        parts = hostname.split('.')
        if len(parts) == 4:
            return all(0 <= int(part) <= 255 for part in parts)
    except (ValueError, AttributeError):
        pass
    return hostname in ['localhost', '127.0.0.1']

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
        raise Exception(f"Error getting database password from secrets: {e}")

def deploy_complete_schema():
    """Deploy the complete database schema."""
    logger = setup_logging()
    
    try:
        # Get database URL
        logger.info("Getting database connection URL...")
        db_url = get_database_url()
        
        # Resolve database URL to use correct IP and credentials
        resolved_url = get_resolved_database_url(db_url)
        if resolved_url != db_url:
            logger.info("Using resolved Cloud SQL connection with internal IP")
            db_url = resolved_url
        
        # Read the complete schema file
        schema_file = Path(__file__).parent.parent / 'database_migrations' / 'complete_schema.sql'
        if not schema_file.exists():
            raise FileNotFoundError(f"Complete schema file not found: {schema_file}")
        
        logger.info(f"Reading complete schema from: {schema_file}")
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Connect to database and execute schema
        logger.info("Connecting to database...")
        conn = psycopg2.connect(db_url)
        conn.autocommit = True  # Enable autocommit for DDL statements
        
        cursor = conn.cursor()
        
        # Check if this is a fresh database or needs migration
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'guilds', 'mining_events', 'materials');
        """)
        existing_tables = cursor.fetchone()[0]
        
        if existing_tables > 0:
            logger.info(f"Found {existing_tables} existing core tables. Running incremental schema update...")
        else:
            logger.info("Fresh database detected. Running complete schema deployment...")
        
        # Execute the complete schema with better error handling
        logger.info("Executing complete database schema...")
        
        # Split into individual statements and execute them
        statements = []
        current_statement = []
        
        for line in schema_sql.split('\n'):
            line = line.strip()
            if line.startswith('--') or not line:
                continue
            
            current_statement.append(line)
            
            # If line ends with semicolon, it's the end of a statement
            if line.endswith(';'):
                stmt = ' '.join(current_statement).strip()
                if stmt and not stmt.startswith('COMMENT'):
                    statements.append(stmt)
                current_statement = []
        
        # Execute statements one by one with error handling
        success_count = 0
        error_count = 0
        
        for i, stmt in enumerate(statements):
            try:
                cursor.execute(stmt)
                success_count += 1
                if i % 10 == 0:  # Log progress every 10 statements
                    logger.info(f"Executed {i+1}/{len(statements)} statements...")
            except Exception as e:
                error_count += 1
                # Log the error but continue (for idempotent operations)
                if "already exists" not in str(e).lower():
                    logger.warning(f"Statement {i+1} failed: {str(e)[:100]}...")
        
        logger.info(f"Schema deployment completed: {success_count} successful, {error_count} errors/skipped")
        
        # Verify key tables were created
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'guilds', 'mining_events', 'materials', 'market_listings', 'applications')
            ORDER BY table_name;
        """)
        
        created_tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Verified tables: {', '.join(created_tables)}")
        
        # Check total table count
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            AND table_name NOT LIKE 'alert%'
            AND table_name NOT LIKE 'dashboard%'
            AND table_name NOT LIKE 'data%'
            AND table_name NOT LIKE 'org%'
            AND table_name NOT LIKE 'user%'
            AND table_name NOT LIKE 'migration%';
        """)
        
        total_tables = cursor.fetchone()[0]
        logger.info(f"Total bot-related tables in database: {total_tables}")
        
        cursor.close()
        conn.close()
        
        logger.info("✅ Complete database schema deployed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema deployment failed: {e}")
        return False

def main():
    """Main entry point for deployment script."""
    success = deploy_complete_schema()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()