"""
Discord bot commands for the Red Legion bot.

This package contains all Discord command modules organized by feature:
- market.py: Market-related commands
- loans.py: Loan system commands  
- events.py: Event management commands
- mining.py: Mining results commands
- diagnostics.py: Health and diagnostic commands
- admin.py: Administrative commands
- general.py: Basic bot commands
"""

def register_all_commands(bot):
    """
    Register all command modules with the bot.
    
    Args:
        bot: The Discord bot instance
    """
    from . import market, loans, events, mining, diagnostics, admin, general
    
    # Register commands from each module
    market.register_commands(bot)
    loans.register_commands(bot)
    events.register_commands(bot)
    mining.register_commands(bot)
    diagnostics.register_commands(bot)
    admin.register_commands(bot)
    general.register_commands(bot)
    
    print("✅ All command modules registered successfully")
