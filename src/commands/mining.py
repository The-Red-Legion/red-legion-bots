"""
Mining Commands - DEPRECATED

Mining commands have been moved to the Management Portal web interface.
This module is kept for imports but no longer registers Discord commands.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import for compatibility but don't register commands
from modules.mining import MiningEventManager, VoiceTracker

async def setup(bot):
    """
    DEPRECATED: Mining commands moved to Management Portal.
    This setup function no longer registers any Discord commands.
    """
    print("⚠️ Mining commands deprecated - use Management Portal web interface")