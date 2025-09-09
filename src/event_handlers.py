"""
Legacy event handlers module for backward compatibility.
This file re-exports the new modular event handlers.
"""

from handlers.core import setup as setup_event_handlers
from handlers.voice_tracking import *

# Legacy exports
__all__ = ['setup_event_handlers']