"""
Payroll Module for Red Legion Bot

Universal payroll system for all event types that collect valuable materials.
Supports mining, salvage, combat, hauling, and any future operations.

Commands:
- /payroll mining - Calculate mining session payroll
- /payroll salvage - Calculate salvage operation payroll  
- /payroll combat - Calculate combat mission payroll

Features:
- Participation-based distribution
- Voluntary donation system
- Multiple material type processors
- Unified UI/UX across all event types
"""

from .commands import PayrollCommands
from .core import PayrollCalculator
from .processors import MiningProcessor, SalvageProcessor, CombatProcessor

__all__ = [
    'PayrollCommands',
    'PayrollCalculator',
    'MiningProcessor',
    'SalvageProcessor', 
    'CombatProcessor',
]