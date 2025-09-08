"""
Red Legion Bot - Database Module

This module provides a clean, modern database architecture for the Red Legion Discord Bot.
Completely redesigned from the ground up with proper normalization, relationships, and scalability.

Architecture:
- schemas/: Database schema definitions
- operations/: CRUD operations for each entity
- migrations/: Database migration system
- connection.py: Database connection management
- models.py: Data models and validation

Design Principles:
1. Normalization: Proper database structure to reduce redundancy
2. Relationships: Clear foreign key relationships between entities  
3. Scalability: Support for multiple guilds and concurrent operations
4. Performance: Optimized indexes and query patterns
5. Maintainability: Clear naming conventions and documentation
"""

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
