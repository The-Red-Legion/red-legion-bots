"""
Payroll Commands - Thin Wrapper

Lightweight wrapper that imports and registers the PayrollCommands class
from the payroll module. Maintains Discord.py compatibility while keeping
business logic in the modules package.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.payroll import PayrollCommands

async def setup(bot):
    """
    Setup function for discord.py extension loading.
    
    This function is called by the main bot to register payroll commands.
    The PayrollCommands cog contains app_command.Group setup internally.
    """
    # Add the PayrollCommands cog to the bot
    await bot.add_cog(PayrollCommands(bot))
    
    print("✅ Payroll commands registered")