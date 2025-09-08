"""
Database operations module initialization with explicit imports.
"""

from .operations import (
    # Event operations
    create_mining_event,
    close_mining_event, 
    get_mining_events,
    get_open_mining_events,
    mark_pdf_generated,
    
    # Participation operations
    save_mining_participation,
    get_mining_session_participants,
    
    # Channel operations
    add_mining_channel,
    remove_mining_channel,
    get_mining_channels,
    get_mining_channels_dict,
    
    # Legacy operations
    save_event,
    update_event_end_time,
    get_events,
    get_open_events,
    
    # Mining results
    update_mining_results,
    
    # Market operations
    get_market_items,
    add_market_item,
    
    # Loan operations
    issue_loan,
    
    # Entry operations
    update_entries,
    get_entries,
    
    # Database utilities
    retry_db_operation,
    init_db
)
from .models import init_database

__all__ = [
    # Event operations
    'create_mining_event',
    'close_mining_event', 
    'get_mining_events',
    'get_open_mining_events',
    'mark_pdf_generated',
    
    # Participation operations
    'save_mining_participation',
    'get_mining_session_participants',
    
    # Channel operations
    'add_mining_channel',
    'remove_mining_channel',
    'get_mining_channels',
    'get_mining_channels_dict',
    
    # Legacy operations
    'save_event',
    'update_event_end_time',
    'get_events',
    'get_open_events',
    
    # Mining results
    'update_mining_results',
    
    # Market operations
    'get_market_items',
    'add_market_item',
    
    # Loan operations
    'issue_loan',
    
    # Entry operations
    'update_entries',
    'get_entries',
    
    # Database utilities
    'init_database',
    'retry_db_operation',
    'init_db'
]
