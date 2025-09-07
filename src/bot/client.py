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
            # Load command modules
            await self.load_extension('commands.mining')
            await self.load_extension('commands.admin')
            await self.load_extension('commands.general')
            await self.load_extension('commands.market')
            await self.load_extension('commands.loans')
            await self.load_extension('commands.diagnostics')
            
            # Load event handlers
            await self.load_extension('handlers.voice_tracking')
            await self.load_extension('handlers.core')
            
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
            from ..database import init_database
            from ..config.settings import get_database_url
            
            db_url = get_database_url()
            if db_url:
                init_database(db_url)
                print(f"✅ Database initialized for guild {guild.name}")
        except Exception as e:
            print(f"❌ Error initializing database for guild {guild.name}: {e}")
    
    def run_bot(self):
        """Run the bot with proper error handling."""
        try:
            self.run(DISCORD_CONFIG['TOKEN'])
        except Exception as e:
            print(f"❌ Error starting bot: {e}")
            raise
