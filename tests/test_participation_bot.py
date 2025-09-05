import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.database import init_db
from src.event_handlers import start_logging

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
    assert cursor.execute.call_count == 6
    conn.commit.assert_called_once()
    conn.close.assert_called_once()

def test_start_logging_command(mock_db, mock_discord):
    ctx = Mock()
    ctx.author = Mock()
    ctx.author.voice = None  # Simulate no voice channel
    mock_channel = mock_discord.return_value.get_channel.return_value
    mock_channel.send = AsyncMock()
    ctx.send = AsyncMock()  # Mock ctx.send to handle await
    with patch('src.event_handlers.active_voice_channels', {}):
        bot = Mock()
        bot.loop = Mock()
        bot.get_channel = mock_discord.return_value.get_channel
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_logging(bot, ctx))
        loop.close()
    ctx.send.assert_called_with("You must be in a voice channel to start logging.")  # Check ctx.send instead