import pytest
from unittest.mock import Mock, patch
from bots.participation_bot import init_db, format_duration

@pytest.fixture
def mock_db():
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        yield mock_conn, mock_cursor

def test_init_db(mock_db):
    conn, cursor = mock_db
    init_db()
    cursor.execute.assert_called()
    assert cursor.execute.call_count == 3  # Three CREATE TABLE statements
    conn.commit.assert_called_once()
    conn.close.assert_called_once()

def test_format_duration():
    assert format_duration(3665) == "1h 1m 5s"
    assert format_duration(60) == "0h 1m 0s"
    assert format_duration(0) == "0h 0m 0s"
