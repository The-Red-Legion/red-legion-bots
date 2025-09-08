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
    """Get mining channels as a dictionary for a specific guild."""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Convert database_url to use proxy if running locally
        parsed = urlparse(database_url)
        if parsed.hostname not in ['127.0.0.1', 'localhost']:
            # Try proxy first on port 5433
            proxy_url = database_url.replace(f'{parsed.hostname}:{parsed.port}', '127.0.0.1:5433')
            try:
                conn = psycopg2.connect(proxy_url)
            except psycopg2.OperationalError:
                # If proxy fails, try original URL
                conn = psycopg2.connect(database_url)
        else:
            conn = psycopg2.connect(database_url)
            
        c = conn.cursor()
        
        # Query mining channels for the guild
        c.execute('''
            SELECT channel_name, channel_id 
            FROM mining_channels 
            WHERE guild_id = %s AND is_active = TRUE
            ORDER BY channel_name
        ''', (guild_id,))
        
        rows = c.fetchall()
        channels_dict = {}
        
        for channel_name, channel_id in rows:
            # Use channel names as-is since they're already in the correct format
            channels_dict[channel_name] = str(channel_id)
        
        conn.close()
        return channels_dict
        
    except Exception as e:
        # If database fails, return empty dict to fall back to hardcoded values
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
    """Get mining channels as a list for a specific guild."""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Convert database_url to use proxy if running locally
        parsed = urlparse(database_url)
        if parsed.hostname not in ['127.0.0.1', 'localhost']:
            # Try proxy first on port 5433
            proxy_url = database_url.replace(f'{parsed.hostname}:{parsed.port}', '127.0.0.1:5433')
            try:
                conn = psycopg2.connect(proxy_url)
            except:
                # Fallback to original URL
                conn = psycopg2.connect(database_url)
        else:
            conn = psycopg2.connect(database_url)
            
        c = conn.cursor()
        
        # Query mining channels for the guild
        where_clause = "WHERE guild_id = %s"
        params = [guild_id]
        
        if active_only:
            where_clause += " AND is_active = TRUE"
            
        c.execute(f'''
            SELECT channel_id, channel_name, is_active, created_at
            FROM mining_channels 
            {where_clause}
            ORDER BY channel_name
        ''', params)
        
        rows = c.fetchall()
        conn.close()
        return rows
        
    except Exception as e:
        print(f"Error getting mining channels from database: {e}")
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
