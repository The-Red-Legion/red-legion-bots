"""
Discord bot commands for the Red Legion bot.

This package contains all Discord slash command modules organized by feature:
- market.py: Market-related slash commands  
- loans_new.py: Loan system slash commands
- events_new.py: Event management slash commands
- mining.py: Mining results slash commands
- diagnostics.py: Health and diagnostic slash commands
- admin_new.py: Administrative slash commands
- general.py: Basic bot slash commands

All commands are now using Discord's modern slash command system with "red-" prefix.
"""

async def register_all_commands(bot):
    """
    Register all command modules with the bot using Cog extension loading.
    
    Args:
        bot: The Discord bot instance
    """
    try:
        print("🔄 Loading Red Legion slash command modules...")
        
        # Load new Cog-based slash command modules
        extensions = [
            'commands.diagnostics',      # red-health, red-test, red-dbtest, red-config
            'commands.general',          # red-ping
            'commands.market',           # red-market-list, red-market-add
            'commands.admin_new',        # red-config-refresh, red-restart, etc.
            'commands.loans_new',        # red-loan-request, red-loan-status
            'commands.events_new',       # red-events group commands
            'commands.mining.core',      # red-sunday-mining-*, red-payroll
        ]
        
        for extension in extensions:
            try:
                await bot.load_extension(extension)
                print(f"  ✅ Loaded {extension}")
            except Exception as e:
                print(f"  ❌ Failed to load {extension}: {e}")
                # Continue loading other extensions
                continue
                
        print("✅ All Red Legion slash command modules loaded successfully")
        
        # Sync slash commands with Discord
        try:
            synced = await bot.tree.sync()
            print(f"✅ Synced {len(synced)} slash commands with Discord")
        except Exception as e:
            print(f"⚠️ Failed to sync slash commands: {e}")
        
    except Exception as e:
        print(f"❌ Error loading command modules: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        raise
