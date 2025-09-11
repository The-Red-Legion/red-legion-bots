"""
Mining Commands - Thin Wrapper

Lightweight wrapper that imports and registers the MiningCommands class
from the mining module. Maintains Discord.py compatibility while keeping
business logic in the modules package.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.mining import MiningCommands

async def setup(bot):
    """
    Setup function for discord.py extension loading.
    
    This function is called by the main bot to register mining commands.
    The MiningCommands cog contains app_command.Group setup internally.
    """
    # Add the MiningCommands cog to the bot
    await bot.add_cog(MiningCommands(bot))
    
    print("✅ Mining commands registered")