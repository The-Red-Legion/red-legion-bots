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
