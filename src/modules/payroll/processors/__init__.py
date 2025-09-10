"""
Payroll Processors

Specialized processors for different event types that convert materials to aUEC values.
Each processor handles the unique calculation logic for its event type.
"""

from .mining import MiningProcessor
from .salvage import SalvageProcessor  
from .combat import CombatProcessor

__all__ = [
    'MiningProcessor',
    'SalvageProcessor',
    'CombatProcessor',
]