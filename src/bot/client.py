"""
Main Discord bot client for Red Legion.
"""

import discord
from discord.ext import commands
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import DISCORD_CONFIG, validate_config

class RedLegionBot(commands.Bot):
    """Red Legion Discord Bot with enhanced mining system."""
    
    def __init__(self):
        # Validate configuration before starting
        validate_config()
        
        # Configure intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        intents.guilds = True
        intents.members = True
        
        # Initialize bot
        super().__init__(
            command_prefix='!',
            intents=intents,
            description='Red Legion Discord Bot - Enhanced Mining System'
        )
    
    async def setup_hook(self):
        """Load extensions and setup the bot."""
        try:
            # Load new Cog-based slash command modules
            print("🔄 Loading Red Legion slash command extensions...")
            
            command_extensions = [
                'commands.diagnostics',      # red-health, red-test, red-dbtest, red-config
                'commands.general',          # red-ping
                'commands.market',           # red-market-list, red-market-add
                'commands.admin_new',        # red-config-refresh, red-restart, etc.
                'commands.loans_new',        # red-loan-request, red-loan-status
                'commands.events_new',       # red-events group commands
                'commands.mining.core',      # red-sunday-mining-*, red-payroll
            ]
            
            for extension in command_extensions:
                try:
                    await self.load_extension(extension)
                    print(f"  ✅ Loaded {extension}")
                except Exception as e:
                    print(f"  ❌ Failed to load {extension}: {e}")
                    # Continue loading other extensions
                    continue
            
            # Load event handlers
            handler_extensions = [
                'handlers.voice_tracking',
                'handlers.core'
            ]
            
            for extension in handler_extensions:
                try:
                    await self.load_extension(extension)
                    print(f"  ✅ Loaded {extension}")
                except Exception as e:
                    print(f"  ❌ Failed to load {extension}: {e}")
                    continue
            
            print("✅ All extensions loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading extensions: {e}")
    
    async def on_ready(self):
        """Called when the bot is ready."""
        print(f'\n🤖 {self.user} is now online!')
        print(f'🔗 Connected to {len(self.guilds)} guild(s)')
        
        for guild in self.guilds:
            print(f'  - {guild.name} (ID: {guild.id})')
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            print(f'✅ Synced {len(synced)} slash commands')
        except Exception as e:
            print(f'❌ Failed to sync slash commands: {e}')
    
    async def on_guild_join(self, guild):
        """Called when the bot joins a new guild."""
        print(f'🎉 Joined new guild: {guild.name} (ID: {guild.id})')
        
        # Initialize database for new guild
        try:
            from database_init import init_database_for_deployment
            
            if init_database_for_deployment():
                print(f"✅ Database initialized for guild {guild.name}")
            else:
                print(f"❌ Database initialization failed for guild {guild.name}")
        except Exception as e:
            print(f"❌ Error initializing database for guild {guild.name}: {e}")
    
    def run_bot(self):
        """Run the bot with proper error handling."""
        try:
            self.run(DISCORD_CONFIG['TOKEN'])
        except Exception as e:
            print(f"❌ Error starting bot: {e}")
            raise
