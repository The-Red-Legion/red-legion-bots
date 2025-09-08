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
    try:
        from . import market, loans, events, diagnostics, general
        from .mining import SundayMiningCommands, register_commands as register_mining_commands
        from .admin import register_commands as register_admin_commands
        
        # Register commands from each module
        print("  📦 Registering market commands...")
        market.register_commands(bot)
        
        print("  💰 Registering loan commands...")
        loans.register_commands(bot)
        
        print("  🎯 Registering event commands...")
        events.register_commands(bot)
        
        print("  ⛏️ Registering mining commands...")
        # Mining uses cog pattern, add it directly
        bot.add_cog(SundayMiningCommands(bot))
        # Also register legacy commands for test compatibility
        register_mining_commands(bot)
        
        print("  🔍 Registering diagnostic commands...")
        diagnostics.register_commands(bot)
        
        print("  🛡️ Registering admin commands...")
        register_admin_commands(bot)
        
        print("  🏓 Registering general commands...")
        general.register_commands(bot)
        
        print("✅ All command modules registered successfully")
        
    except Exception as e:
        print(f"❌ Error registering command modules: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        raise
