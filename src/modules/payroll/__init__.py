"""
Payroll Module for Red Legion Bot - API Mode

Universal payroll system for Management Portal integration.
Supports mining, salvage, combat, hauling, and any future operations.

Management Portal Features:
- Web-based payroll calculation interface
- Participation-based distribution algorithms
- Voluntary donation system
- Multiple material type processors
- API endpoints for portal integration

Discord commands have been deprecated in favor of the Management Portal.
Core calculation and processor functionality remains active.
"""

from .core import PayrollCalculator
from .processors import MiningProcessor, SalvageProcessor, CombatProcessor

__all__ = [
    'PayrollCalculator',
    'MiningProcessor',
    'SalvageProcessor',
    'CombatProcessor',
]