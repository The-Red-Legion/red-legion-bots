"""
Database Operations for Red Legion Bot v2.0.0

This module provides CRUD operations and business logic for database entities.
Includes both new architecture classes and legacy compatibility functions.
"""

from typing import List, Optional, Dict, Any
from .connection import DatabaseManager
from .models import User, Guild, MiningEvent, MiningParticipation

class BaseOperations:
    """Base class for database operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

class UserOperations(BaseOperations):
    """User-related database operations."""
    
    def create_user(self, user: User) -> bool:
        """Create a new user."""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (user_id, username, display_name, first_seen, last_seen, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    display_name = EXCLUDED.display_name,
                    last_seen = EXCLUDED.last_seen,
                    updated_at = CURRENT_TIMESTAMP
            """, (user.user_id, user.username, user.display_name, 
                  user.first_seen, user.last_seen, user.is_active))
            return True
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            if row:
                return User(**row)
            return None

class GuildOperations(BaseOperations):
    """Guild-related database operations."""
    
    def create_guild(self, guild: Guild) -> bool:
        """Create a new guild."""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO guilds (guild_id, name, owner_id, is_active)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (guild_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    owner_id = EXCLUDED.owner_id,
                    updated_at = CURRENT_TIMESTAMP
            """, (guild.guild_id, guild.name, guild.owner_id, guild.is_active))
            return True
    
    def get_guild(self, guild_id: str) -> Optional[Guild]:
        """Get a guild by ID."""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute("SELECT * FROM guilds WHERE guild_id = %s", (guild_id,))
            row = cursor.fetchone()
            if row:
                return Guild(**row)
            return None

# Legacy functions - these will be properly implemented later
def init_db(database_url):
    """Legacy function - initialize database"""
    from database import init_database
    return init_database()

def get_market_items(database_url):
    """Legacy function - get market items"""
    return []

def add_market_item(database_url, name, price, stock):
    """Legacy function - add market item"""
    pass

def get_mining_channels_dict(database_url, guild_id):
    """Legacy function - get mining channels"""
    return {}

def issue_loan(database_url, user_id, amount, issued_date, due_date):
    """Legacy function - issue loan"""
    pass

def save_mining_participation(database_url, *args, **kwargs):
    """Legacy function - save mining participation"""
    pass

def add_mining_channel(database_url, guild_id, channel_id, channel_name, description=None):
    """Legacy function - add mining channel"""
    pass

def remove_mining_channel(database_url, guild_id, channel_id):
    """Legacy function - remove mining channel"""
    return True

def get_mining_channels(database_url, guild_id, active_only=True):
    """Legacy function - get mining channels"""
    return []

def migrate_schema(database_url):
    """Legacy function - migrate schema"""
    pass

def close_mining_event(database_url, event_id, total_value=None):
    """Legacy function - close mining event"""
    pass

def mark_pdf_generated(database_url, event_id):
    """Legacy function - mark PDF generated"""
    pass

def get_mining_session_participants(database_url, *args, **kwargs):
    """Legacy function - get mining session participants"""
    return []

def create_mining_event(database_url, guild_id, event_date=None, event_name="Sunday Mining"):
    """Legacy function - create mining event"""
    return None

def get_open_mining_events(database_url, guild_id=None):
    """Legacy function - get open mining events"""
    return []

def save_event(database_url, channel_id, channel_name, event_name, start_time):
    """Legacy function - save event"""
    pass

def update_event_end_time(database_url, channel_id, end_time):
    """Legacy function - update event end time"""
    pass

def get_mining_events(database_url, guild_id, event_date=None):
    """Legacy function - get mining events"""
    return []

def update_entries(database_url, member_id, month_year):
    """Legacy function - update entries"""
    pass

def get_entries(database_url, month_year):
    """Legacy function - get entries"""
    return []

__all__ = [
    'init_db',
    'get_market_items',
    'add_market_item',
    'get_mining_channels_dict',
    'issue_loan',
    'save_mining_participation',
    'add_mining_channel',
    'remove_mining_channel',
    'get_mining_channels',
    'migrate_schema',
    'close_mining_event',
    'mark_pdf_generated',
    'get_mining_session_participants',
    'create_mining_event',
    'get_open_mining_events',
    'save_event',
    'update_event_end_time',
    'get_mining_events',
    'update_entries',
    'get_entries',
]
