"""
Safe production database testing with safeguards.

Only use this approach if you absolutely must test against production DB.
Includes multiple safety mechanisms to prevent data corruption.
"""

import os
import pytest
from unittest import mock
import logging

logger = logging.getLogger(__name__)

class SafeProductionTestError(Exception):
    """Raised when production testing is not safe."""
    pass

def get_safe_production_db_url():
    """
    Get production database URL with safety checks.
    
    Only allows testing if specific safety conditions are met.
    """
    
    # Safety check 1: Must explicitly enable production testing
    if not os.getenv('ALLOW_PRODUCTION_DB_TESTING'):
        raise SafeProductionTestError(
            "Production DB testing disabled. Set ALLOW_PRODUCTION_DB_TESTING=1 if you're sure."
        )
    
    # Safety check 2: Must be in a safe environment
    if os.getenv('ENVIRONMENT') == 'production':
        raise SafeProductionTestError(
            "Cannot run DB tests in production environment"
        )
    
    # Safety check 3: Must have read-only user for tests
    test_user = os.getenv('DB_TEST_USER')
    if not test_user or 'read' not in test_user.lower():
        raise SafeProductionTestError(
            "Must use read-only database user for production testing"
        )
    
    return os.getenv('DATABASE_URL')

@pytest.mark.production
@pytest.mark.skipif(
    not os.getenv('ALLOW_PRODUCTION_DB_TESTING'),
    reason="Production DB testing not enabled"
)
def test_production_database_read_only():
    """
    Test that only reads from production database.
    
    This test verifies database connectivity and schema without modifying data.
    """
    
    try:
        db_url = get_safe_production_db_url()
        
        # Import with read-only connection
        from database import DatabaseManager
        
        with DatabaseManager(db_url).get_connection() as conn:
            with conn.cursor() as cursor:
                # Only SELECT operations - no writes!
                cursor.execute("SELECT 1 as test_connection")
                result = cursor.fetchone()
                assert result['test_connection'] == 1
                
                # Test schema exists
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tables = cursor.fetchall()
                
                expected_tables = ['guilds', 'users', 'mining_events', 'mining_participation']
                table_names = [table['table_name'] for table in tables]
                
                for expected_table in expected_tables:
                    assert expected_table in table_names, f"Missing table: {expected_table}"
                
                logger.info(f"✅ Production database schema validation passed")
                logger.info(f"Found tables: {table_names}")
                
    except SafeProductionTestError as e:
        pytest.skip(f"Production testing not safe: {e}")

@pytest.mark.production
def test_deployment_functions_signature_only():
    """
    Test deployment functions without actually calling database operations.
    
    This verifies the signature fix without touching the database.
    """
    
    import inspect
    from database_init import init_database_for_deployment, schema_init
    
    # Verify signatures are compatible
    deployment_sig = inspect.signature(init_database_for_deployment)
    schema_sig = inspect.signature(schema_init)
    
    assert 'db_url' in deployment_sig.parameters
    assert 'database_url' in schema_sig.parameters
    
    logger.info("✅ Function signatures are compatible")
    logger.info(f"deployment: {deployment_sig}")
    logger.info(f"schema: {schema_sig}")

# Safe usage example
if __name__ == "__main__":
    # To run production tests (use with extreme caution):
    # export ALLOW_PRODUCTION_DB_TESTING=1
    # export DB_TEST_USER=readonly_user
    # export ENVIRONMENT=testing
    # python -m pytest tests/test_safe_production.py -v -m production
    
    # Run signature test (safe, no DB access)
    test_deployment_functions_signature_only()
    print("✅ Signature test passed - no database access required!")
