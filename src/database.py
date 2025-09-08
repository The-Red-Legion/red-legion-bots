"""
Legacy Database Module

This file provides backward compatibility for imports from the old 'database.py' structure.
All functions are re-exported from the new modular database package.
"""

# Import everything from the new database package
from database import *
from database.operations import *

# Maintain legacy compatibility
__all__ = [
    # All exports from new database module
    'DatabaseManager',
    'get_connection', 
    'get_cursor',
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
    'GuildOperations',
    'UserOperations',
    'MiningOperations',
    'EconomyOperations',
    'init_database',
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
]