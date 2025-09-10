"""
Commands Package - Thin Command Layer

This package provides Discord command registration while keeping business logic 
in the modules package. Each command file here is a lightweight wrapper that
imports and registers the actual command classes from their respective modules.

Architecture:
- /commands/     <- Thin wrappers for Discord.py compatibility  
- /modules/      <- Actual business logic and implementations

This approach maintains clean separation while ensuring the bot can load
commands in the expected way.
"""

# Import command classes from modules
from modules.mining import MiningCommands
from modules.payroll import PayrollCommands

# Export for easy importing
__all__ = [
    'MiningCommands',
    'PayrollCommands',
]

# Command registration mapping for main bot
COMMAND_MODULES = {
    'mining': 'commands.mining',
    'payroll': 'commands.payroll',
}

async def setup_all_commands(bot):
    """
    Setup all command modules with the bot.
    Called by main bot during initialization.
    """
    try:
        # Load mining commands
        from . import mining
        await mining.setup(bot)
        
        # Load payroll commands  
        from . import payroll
        await payroll.setup(bot)
        
        print("✅ All command modules loaded successfully")
        
    except Exception as e:
        print(f"❌ Error loading command modules: {e}")
        raise