"""
Test to catch deployment initialization signature issues.

This test specifically tests the deployment path that was failing in production.
"""

import pytest
from unittest.mock import patch, MagicMock

def test_deployment_init_function_signatures():
    """
    Test that deployment initialization functions have correct signatures.
    This test would have caught the signature mismatch that caused deployment failure.
    """
    
    # Test 1: database_init.init_database_for_deployment signature
    with patch('database_init.get_database_url') as mock_get_url, \
         patch('database_init.DatabaseManager') as mock_db_manager, \
         patch('database_init.schema_init') as mock_schema_init:
        
        mock_get_url.return_value = "postgresql://test:test@localhost/test"
        mock_schema_init.return_value = True
        
        from database_init import init_database_for_deployment
        
        # Should work with no arguments
        result = init_database_for_deployment()
        assert result is True
        
        # Should work with db_url argument
        result = init_database_for_deployment("postgresql://test:test@localhost/test")
        assert result is True
        
        # Verify schema_init was called with database_url
        mock_schema_init.assert_called_with("postgresql://test:test@localhost/test")

def test_schema_init_function_signature():
    """
    Test that the schema_init function imported in database_init accepts database_url parameter.
    """
    
    with patch('database.schemas.DatabaseManager') as mock_db_manager:
        mock_db_manager.return_value.get_connection.return_value.__enter__ = MagicMock()
        mock_db_manager.return_value.get_connection.return_value.__exit__ = MagicMock()
        
        # This should work without error - importing the version that accepts parameters
        from database.schemas import init_database
        
        # Test that it accepts database_url parameter
        import inspect
        sig = inspect.signature(init_database)
        
        # Should have database_url parameter with default None
        assert 'database_url' in sig.parameters
        assert sig.parameters['database_url'].default is None

def test_main_py_deployment_flow():
    """
    Test the actual deployment flow from main.py to ensure it works end-to-end.
    """
    
    with patch('database_init.get_database_url') as mock_get_url, \
         patch('database_init.DatabaseManager') as mock_db_manager, \
         patch('database_init.schema_init') as mock_schema_init:
        
        mock_get_url.return_value = "postgresql://test:test@localhost/test" 
        mock_schema_init.return_value = True
        
        # Import and call the exact same function that main.py calls
        from database_init import init_database_for_deployment
        
        # This is the exact call pattern from main.py
        result = init_database_for_deployment()
        
        # Verify it works
        assert result is True
        
        # Verify schema_init was called with the database URL (as expected)
        mock_schema_init.assert_called_with("postgresql://test:test@localhost/test")

if __name__ == "__main__":
    # Run the specific tests
    test_deployment_init_function_signatures()
    test_schema_init_function_signature() 
    test_main_py_deployment_flow()
    print("✅ All deployment signature tests passed!")
