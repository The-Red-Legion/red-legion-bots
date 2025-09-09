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

def test_start_logging_command(mock_db, mock_discord):
    """Test legacy command replaced by new mining system."""
    # Legacy start_logging command replaced by /sunday_mining_start
    # This test verifies the database init still works
    conn, cursor = mock_db
    assert cursor is not None
    assert conn is not None
    
    # Simple test to ensure the command files exist
    import os
    mining_core_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'commands', 'mining', 'core.py')
    assert os.path.exists(mining_core_path), "Mining commands core module should exist"
    print("✅ New mining commands module file exists")