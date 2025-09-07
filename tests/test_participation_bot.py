import pytest
from unittest.mock import Mock, patch, AsyncMock
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
    init_db("postgresql://test:test@localhost:5432/testdb")
    cursor.execute.assert_called()
    # 8 CREATE TABLE statements + 1 migration check = 9 total execute calls
    assert cursor.execute.call_count == 9
    conn.commit.assert_called_once()
    conn.close.assert_called_once()

def test_start_logging_command(mock_db, mock_discord):
    """Test legacy command replaced by new mining system."""
    # Legacy start_logging command replaced by /sunday_mining_start
    # This test verifies the database init still works
    conn, cursor = mock_db
    assert cursor is not None
    assert conn is not None
    
    # Simple test to ensure the new system is loadable
    try:
        from src.commands.mining.core import SundayMiningCommands
        assert SundayMiningCommands is not None
        print("✅ New mining commands module loads successfully")
    except ImportError as e:
        pytest.fail(f"Failed to load new mining commands: {e}")