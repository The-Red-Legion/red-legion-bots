"""
Red Legion Discord Bot - Enhanced Mining System

A comprehensive Discord bot for managing Sunday mining operations,
voice tracking, payroll calculations, and community management.
"""

__version__ = "2.0.0"
__author__ = "Red Legion"
__description__ = "Enhanced Sunday Mining Discord Bot"

from .bot import RedLegionBot
from .config.settings import validate_config
from .database import init_database

__all__ = [
    'RedLegionBot',
    'validate_config', 
    'init_database'
]
