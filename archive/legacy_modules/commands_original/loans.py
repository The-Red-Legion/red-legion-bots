"""
Legacy loans commands module for backward compatibility.
This file re-exports the new loans subcommand module.
"""

from .loans_subcommand import *

# Legacy exports
__all__ = [
    'LoansCommands',
    'setup'
]