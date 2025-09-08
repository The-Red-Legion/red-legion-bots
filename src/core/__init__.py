"""
Core utilities and bot setup modules for the Red Legion Discord bot.

This package contains:
- bot_setup.py: Bot initialization and configuration
- decorators.py: Shared decorators and utilities
"""

from .bot_setup import create_bot_instance
from .decorators import (
    has_org_role,
    standard_cooldown,
    admin_only,
    error_handler
)

__all__ = [
    'create_bot_instance',
    'has_org_role',
    'standard_cooldown', 
    'admin_only',
    'error_handler'
]
