import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import init_db
# Legacy event_handlers replaced by new modular system
# from event_handlers import start_logging

@pytest.fixture
def mock_db():
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.side_effect = lambda url: mock_conn
        yield mock_conn, mock_cursor

@pytest.fixture
def mock_discord():
    with patch('discord.Client') as mock_client:
        mock_client_instance = Mock()
        mock_client_instance.get_channel = Mock(return_value=Mock())
        mock_client_instance.get_channel.return_value.send = AsyncMock()
        mock_client.return_value = mock_client_instance
        yield mock_client

def test_init_db(mock_db):
    conn, cursor = mock_db
    
    # Mock the DatabaseManager initialization
    with patch('database.connection.initialize_database') as mock_init_db:
        mock_db_manager = Mock()
        mock_cursor_context = Mock()
        mock_cursor_context.__enter__ = Mock(return_value=cursor)
        mock_cursor_context.__exit__ = Mock(return_value=None)
        mock_db_manager.get_cursor.return_value = mock_cursor_context
        mock_init_db.return_value = mock_db_manager
        
        result = init_db("postgresql://test:test@localhost:5432/testdb")
        
        # Verify that database initialization was attempted
        mock_init_db.assert_called_once_with("postgresql://test:test@localhost:5432/testdb")
        print("✅ init_db function completed successfully")

def test_mining_module_architecture(mock_db, mock_discord):
    """Test new modules architecture for mining system."""
    # New modules architecture replaces legacy scattered commands
    # This test verifies the new structure exists
    conn, cursor = mock_db
    assert cursor is not None
    assert conn is not None
    
    # Test that new modules architecture exists
    import os
    base_path = os.path.join(os.path.dirname(__file__), '..', 'src')
    
    # Check new modules structure
    mining_module_path = os.path.join(base_path, 'modules', 'mining', 'commands.py')
    payroll_module_path = os.path.join(base_path, 'modules', 'payroll', 'commands.py')
    mining_wrapper_path = os.path.join(base_path, 'commands', 'mining.py')
    payroll_wrapper_path = os.path.join(base_path, 'commands', 'payroll.py')
    
    assert os.path.exists(mining_module_path), "Mining module should exist at src/modules/mining/commands.py"
    assert os.path.exists(payroll_module_path), "Payroll module should exist at src/modules/payroll/commands.py"
    assert os.path.exists(mining_wrapper_path), "Mining command wrapper should exist at src/commands/mining.py"
    assert os.path.exists(payroll_wrapper_path), "Payroll command wrapper should exist at src/commands/payroll.py"
    
    print("✅ New modules architecture verified")
    print("✅ Mining and payroll modules exist")
    print("✅ Command wrappers exist")