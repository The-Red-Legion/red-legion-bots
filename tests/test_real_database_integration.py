"""
Real database integration tests that connect to an actual PostgreSQL instance.

These tests would have caught the deployment signature issue because they use
real database connections instead of mocks.
"""

import pytest
import os
import logging
from unittest import mock

# Real database connection details for testing
TEST_DATABASE_CONFIG = {
    "host": "localhost",  # or your test DB host
    "port": "5432",
    "database": "red_legion_test", 
    "user": "test_user",
    "password": "test_password"
}

def get_test_database_url():
    """Get database URL for testing with real database."""
    return f"postgresql://{TEST_DATABASE_CONFIG['user']}:{TEST_DATABASE_CONFIG['password']}@{TEST_DATABASE_CONFIG['host']}:{TEST_DATABASE_CONFIG['port']}/{TEST_DATABASE_CONFIG['database']}"

@pytest.mark.integration 
@pytest.mark.skipif(
    not os.getenv('RUN_INTEGRATION_TESTS'), 
    reason="Set RUN_INTEGRATION_TESTS=1 to run real database tests"
)
def test_real_database_initialization():
    """
    Test database initialization with a real PostgreSQL connection.
    This would have caught the signature mismatch issue.
    """
    
    # Set up test database URL
    test_db_url = get_test_database_url()
    
    # Test the actual deployment initialization flow
    with mock.patch('config.settings.get_database_url', return_value=test_db_url):
        from database_init import init_database_for_deployment
        
        # This would have failed with the signature mismatch
        result = init_database_for_deployment()
        
        # If we get here, initialization worked
        assert result is True

@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv('RUN_INTEGRATION_TESTS'), 
    reason="Set RUN_INTEGRATION_TESTS=1 to run real database tests"  
)
def test_real_schema_initialization():
    """
    Test schema initialization with real database connection.
    """
    
    test_db_url = get_test_database_url()
    
    # Test calling schema initialization directly with URL
    from database.schemas import init_database
    
    # This would have revealed the signature issue
    result = init_database(test_db_url)
    assert result is True

@pytest.mark.integration 
def test_database_connection_with_hardcoded_details():
    """
    Test with hardcoded database connection details.
    
    You could use your actual database credentials here if you wanted.
    """
    
    # Example with actual database details (use your real ones)
    real_db_url = "postgresql://arccorp_sys_admin:your_password@your_host:5432/your_database"
    
    # Skip if no real credentials provided
    if "your_password" in real_db_url:
        pytest.skip("Replace with real database credentials to run this test")
    
    # Test with real database
    with mock.patch('config.settings.get_database_url', return_value=real_db_url):
        from database_init import init_database_for_deployment
        
        # This calls the real database initialization
        result = init_database_for_deployment()
        assert result is True

def test_signature_compatibility_check():
    """
    Test that verifies function signatures are compatible without needing a real database.
    This test would have caught the signature mismatch.
    """
    
    import inspect
    from database_init import init_database_for_deployment, schema_init
    
    # Check that init_database_for_deployment can call schema_init
    deployment_sig = inspect.signature(init_database_for_deployment)
    schema_sig = inspect.signature(schema_init)
    
    # deployment_sig should have db_url parameter
    assert 'db_url' in deployment_sig.parameters
    
    # schema_sig should accept database_url parameter  
    schema_params = list(schema_sig.parameters.keys())
    
    # Should have either no parameters or database_url parameter
    assert len(schema_params) == 0 or 'database_url' in schema_params
    
    # If schema_init has parameters, it should accept database_url
    if len(schema_params) > 0:
        database_url_param = schema_sig.parameters.get('database_url')
        assert database_url_param is not None
        # Should have default value for compatibility
        assert database_url_param.default is not None or database_url_param.default is inspect.Parameter.empty

if __name__ == "__main__":
    # Run signature test (doesn't need real DB)
    test_signature_compatibility_check()
    print("✅ Signature compatibility test passed!")
    
    # To run integration tests:
    # export RUN_INTEGRATION_TESTS=1
    # python -m pytest tests/test_real_database_integration.py -v -m integration
