"""
Mining Module for Red Legion Bot - API Mode

Handles mining operations for Management Portal integration:
- Voice channel participation tracking (Core functionality)
- Event management through API endpoints
- Integration with Management Portal for session control

Discord commands have been deprecated in favor of the Management Portal.
Core voice tracking functionality remains active.
"""

from .events import MiningEventManager
from .participation import VoiceTracker

__all__ = [
    'MiningEventManager',
    'VoiceTracker',
]