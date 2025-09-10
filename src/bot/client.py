"""
Main Discord bot client for Red Legion.
"""

import discord
from discord.ext import commands
import sys
from pathlib import Path
from datetime import datetime

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
            
            # New modules architecture - only load commands that exist
            extensions = [
                'commands.mining',             # Wrapper for mining module (/mining start, /mining stop)
                'commands.payroll',            # Wrapper for payroll module (/payroll calculate)
                'commands.test_data',          # Test data generation (/test-data create, /test-data delete)
                'commands.admin',              # Admin commands (/admin delete-event, /admin voice-diagnostic)
                'commands.diagnostics',        # Diagnostic tools (/diagnostics voice, /diagnostics channels)
            ]
            
            for extension in extensions:
                try:
                    await self.load_extension(extension)
                    print(f"  ✅ Loaded {extension}")
                except Exception as e:
                    print(f"  ❌ Failed to load {extension}: {e}")
                    # Continue loading other extensions
                    continue
            
            # Load event handlers (only load what exists)
            handler_extensions = [
                'handlers.voice_tracking',     # Voice channel participation tracking
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
        print(f'🤖 {self.user} is now online and ready!')
        print(f'📡 Connected to {len(self.guilds)} guild(s)')
        
        # Initialize UEX cache service
        try:
            print("🗄️ Starting UEX API cache service...")
            from services.uex_cache import initialize_uex_cache
            await initialize_uex_cache()
            print("✅ UEX cache service started")
        except Exception as e:
            print(f"❌ Failed to start UEX cache service: {e}")
        
        # Sync slash commands with Discord
        try:
            print("🔄 Syncing slash commands...")
            synced = await self.tree.sync()
            print(f"✅ Synced {len(synced)} slash command(s) to Discord")
        except Exception as e:
            print(f"❌ Failed to sync commands: {e}")

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
        
        # Sync commands for the new guild
        try:
            print(f"🔄 Syncing commands for guild {guild.name}...")
            synced = await self.tree.sync(guild=guild)
            print(f"✅ Synced {len(synced)} command(s) for {guild.name}")
        except Exception as e:
            print(f"❌ Failed to sync commands for {guild.name}: {e}")
    
    async def close(self):
        """Cleanup when bot is closing."""
        try:
            print("🛑 Shutting down UEX cache service...")
            from services.uex_cache import shutdown_uex_cache
            await shutdown_uex_cache()
            print("✅ UEX cache service stopped")
        except Exception as e:
            print(f"⚠️ Error stopping UEX cache: {e}")
        
        await super().close()

    def run_bot(self):
        """Run the bot with proper error handling."""
        try:
            self.run(DISCORD_CONFIG['TOKEN'])
        except Exception as e:
            print(f"❌ Error starting bot: {e}")
            raise
