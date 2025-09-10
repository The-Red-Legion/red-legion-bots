"""
Red Legion Bot Modules

Clean, domain-driven architecture for Star Citizen organization management.
Each module handles a complete domain (mining, payroll, etc.) with all related functionality.
"""

from . import mining
from . import payroll

__all__ = [
    'mining',
    'payroll',
]

__version__ = '2.0.0'