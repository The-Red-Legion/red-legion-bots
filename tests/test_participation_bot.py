import pytest
from unittest.mock import Mock, patch
from src.database import init_db

@pytest.fixture
def mock_db():
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        # Simulate database_url being passed
        mock_connect.side_effect = lambda url: mock_conn
        yield mock_conn, mock_cursor

def test_init_db(mock_db):
    conn, cursor = mock_db
    # Pass a dummy database_url to match the function signature
    init_db("postgresql://test:test@localhost:5432/testdb")
    cursor.execute.assert_called()
    assert cursor.execute.call_count == 6  # Six CREATE TABLE statements
    conn.commit.assert_called_once()
    conn.close.assert_called_once()