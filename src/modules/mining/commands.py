"""
Mining Commands for Red Legion Bot - DEPRECATED

These commands have been moved to the Management Portal web interface.
This file now only contains core management classes for voice tracking.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .events import MiningEventManager
from .participation import VoiceTracker

# Note: All Discord commands have been moved to the Management Portal
# This module now only exports the core management classes for API use