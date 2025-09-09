"""
Legacy market commands module for backward compatibility.
This file re-exports the new market subcommand module.
"""

from .market_subcommand import *

# Legacy exports
__all__ = [
    'MarketCommands',
    'setup'
]