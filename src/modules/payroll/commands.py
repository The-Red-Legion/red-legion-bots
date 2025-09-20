"""
Payroll Commands for Red Legion Bot - DEPRECATED

These commands have been moved to the Management Portal web interface.
This file now only contains core processor classes for API use.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .core import PayrollCalculator
from .processors import MiningProcessor, SalvageProcessor, CombatProcessor

# Note: All Discord commands have been moved to the Management Portal
# This module now only exports the core processor classes for API use