"""
Database module for Red Legion Bot - Version 2.0.0

Complete rebuild with modern PostgreSQL architecture:
- Proper normalization and relationships
- Connection pooling and transaction management  
- Comprehensive dataclass models with type hints
- Organized CRUD operations by entity
- Scalable and maintainable design

Key Features:
- DatabaseManager: Connection pooling and health monitoring
- Models: Clean dataclass models for all entities
- Operations: Organized CRUD operations (GuildOperations, UserOperations, etc.)
- Schema: Complete SQL schema with proper relationships and indexes
"""

from .connection import DatabaseManager, get_connection, get_cursor
from .models import *
from .operations import *
from .schemas import init_database

# Legacy compatibility imports and aliases
init_db = init_database  # Alias for backward compatibility

# Legacy function stubs for backward compatibility
def get_market_items(db_url):
    """Legacy function - will be implemented with new operations"""
    return []

def add_market_item(db_url, name, price, stock):
    """Legacy function - will be implemented with new operations"""
    pass

# Import all functions from operations to make them available
from .connection import DatabaseManager, get_connection, get_cursor, initialize_database
from .models import *
from .operations import *
from .schemas import init_database

def issue_loan(db_url, user_id, amount, issued_date, due_date):
    """Legacy function - will be implemented with new operations"""
    pass

def save_mining_participation(db_url, *args, **kwargs):
    """Legacy function - will be implemented with new operations"""
    pass

def add_mining_channel(db_url, guild_id, channel_id, channel_name, description=None):
    """Legacy function - will be implemented with new operations"""
    pass

def remove_mining_channel(db_url, guild_id, channel_id):
    """Legacy function - will be implemented with new operations"""
    return True

def get_mining_channels(db_url, guild_id, active_only=True):
    """Legacy function - will be implemented with new operations"""
    return []

def migrate_schema(db_url):
    """Legacy function - will be implemented with new operations"""
    pass

def close_mining_event(db_url, event_id, total_value=None):
    """Legacy function - will be implemented with new operations"""
    pass

def mark_pdf_generated(db_url, event_id):
    """Legacy function - will be implemented with new operations"""
    pass

def get_mining_session_participants(db_url, *args, **kwargs):
    """Legacy function - will be implemented with new operations"""
    return []

def create_mining_event(db_url, guild_id, event_date=None, event_name="Sunday Mining"):
    """Legacy function - will be implemented with new operations"""
    return None

def get_open_mining_events(db_url, guild_id=None):
    """Legacy function - will be implemented with new operations"""
    return []

__version__ = "2.0.0"
__all__ = [
    # Connection management
    'DatabaseManager',
    'get_connection', 
    'get_cursor',
    
    # Models
    'Guild',
    'User', 
    'GuildMembership',
    'MiningEvent',
    'MiningChannel',
    'MiningParticipation',
    'Material',
    'MiningYield',
    'Loan',
    'LoanStatus',
    'MiningEventStatus',
    
    # Operations
    'GuildOperations',
    'UserOperations',
    'MiningOperations',
    'EconomyOperations',
    
    # Schema
    'init_database',
    'init_db',  # Legacy alias
    
    # Legacy functions (compatibility layer)
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
]

from .connection import DatabaseManager, get_connection, get_cursor, initialize_database
from .models import *
from .operations import *
from .schemas import init_database

__all__ = [
    'DatabaseManager',
    'get_connection',
    'get_cursor', 
    'initialize_database',
    'init_database',
    'GuildOperations',
    'UserOperations',
    # Models
    'Guild',
    'User',
    'GuildMembership',
    'MiningEvent',
    'MiningChannel',
    'MiningParticipation',
    'Material',
    'MiningYield',
    'Loan',
    'EventStatus',
    'LoanStatus',
    'MaterialCategory',
]

# Version tracking for database schema
DATABASE_VERSION = '2.0.0'
