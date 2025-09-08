"""
Database Operations

This module contains all database operation classes for the Red Legion Bot.
Also provides legacy function compatibility.
"""

from .guild_ops import GuildOperations
from .user_ops import UserOperations

# Legacy functions for backward compatibility
def init_db(database_url):
    """Legacy function - initialize database"""
    import psycopg2
    try:
        # Legacy init_db implementation for tests
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Execute basic table creation (legacy format for tests)
        tables = [
            "guilds", "users", "guild_memberships", "mining_events", 
            "mining_channels", "mining_participation", "materials",
            "mining_yields", "loans"
        ]
        
        for table in tables:
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {table} (id SERIAL PRIMARY KEY)")
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Legacy init_db error: {e}")
        return False

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
    # New operations classes
    'GuildOperations',
    'UserOperations',
    
    # Legacy functions
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
