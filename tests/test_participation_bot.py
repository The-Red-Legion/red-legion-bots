import pytest
from unittest.mock import Mock, patch
from src.database import init_db
from src.participation_bot import bot  # Assuming bot is imported or defined

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
        mock_client.return_value = Mock()
        yield mock_client

def test_init_db(mock_db):
    conn, cursor = mock_db
    init_db("postgresql://test:test@localhost:5432/testdb")
    cursor.execute.assert_called()
    assert cursor.execute.call_count == 6  # Six CREATE TABLE statements
    conn.commit.assert_called_once()
    conn.close.assert_called_once()

def test_start_logging_command(mock_db, mock_discord):
    # Mock the context and bot behavior
    ctx = Mock()
    ctx.author.voice = Mock()
    ctx.author.voice.channel = Mock()
    ctx.author.voice.channel.id = "12345"
    bot.get_channel = Mock(return_value=Mock(send=Mock()))

    # Import and call the actual start_logging function
    from src.event_handlers import start_logging
    with patch('src.event_handlers.active_voice_channels', {}):
        bot.loop = Mock()  # Mock the event loop if needed
        bot.loop.run_until_complete(start_logging(bot, ctx))

    # Verify the command sends a message
    bot.get_channel.assert_called()
    bot.get_channel.return_value.send.assert_called()