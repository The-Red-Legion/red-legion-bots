"""
Legacy event handlers module (Compatibility)

This file exists for backward compatibility.
Event handling is now distributed across handlers/ modules.
"""

import warnings

# Show deprecation warning
warnings.warn(
    "event_handlers.py is deprecated. Use handlers.voice_tracking and handlers.core instead.", 
    DeprecationWarning, 
    stacklevel=2
)

# Legacy compatibility functions at module level
async def setup_event_handlers():
    """Legacy setup function - redirects to new modular system."""
    print("⚠️ setup_event_handlers is deprecated. Event handlers are now auto-loaded.")
    return True

def on_voice_state_update(*args, **kwargs):
    """Legacy voice state update handler."""
    print("⚠️ Voice tracking moved to handlers.voice_tracking")
    
def start_voice_tracking(*args, **kwargs):
    """Legacy voice tracking start function."""
    print("⚠️ Voice tracking moved to handlers.voice_tracking")
    
def stop_voice_tracking(*args, **kwargs):
    """Legacy voice tracking stop function."""
    print("⚠️ Voice tracking moved to handlers.voice_tracking")

# Note: The actual implementations are now in:
# - handlers.voice_tracking for voice state management  
# - handlers.core for core Discord event handling
