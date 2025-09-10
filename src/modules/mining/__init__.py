"""
Mining Module for Red Legion Bot

Handles all mining operations including:
- Mining session management (/mining start, /mining stop) 
- Voice channel participation tracking
- Event creation with unified database schema
- Integration with payroll system for ore distribution

This module focuses solely on mining operations. Payroll calculations
are handled by the shared payroll module.
"""

from .commands import MiningCommands
from .events import MiningEventManager
from .participation import VoiceTracker

__all__ = [
    'MiningCommands',
    'MiningEventManager', 
    'VoiceTracker',
]