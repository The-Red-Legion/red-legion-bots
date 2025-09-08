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
            
            # Core command extensions with proper "red-" prefix commands
            extensions = [
                'commands.diagnostics',      # red-health, red-test, red-dbtest, red-config
                'commands.general',          # red-ping
                'commands.market',           # red-market-list, red-market-add
                'commands.admin',            # red-config-refresh, red-restart, etc.
                'commands.loans',            # red-loan-request, red-loan-status
                'commands.events',           # red-events group commands
                'commands.mining.core',      # red-sunday-mining-*, red-payroll
            ]
            
            for extension in extensions:
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
        
        # Debug: Check what commands we have locally before sync
        local_commands = [cmd.name for cmd in self.tree.get_commands() if hasattr(cmd, 'name')]
        print(f'🔍 Local commands loaded: {len(local_commands)}')
        
        # Count red- prefix commands
        red_commands = [cmd for cmd in local_commands if cmd.startswith('red-')]
        other_commands = [cmd for cmd in local_commands if not cmd.startswith('red-')]
        
        print(f'✅ Commands with red- prefix: {len(red_commands)}')
        if other_commands:
            print(f'⚠️ Commands without red- prefix: {len(other_commands)}')
            for cmd in other_commands:
                print(f'  � {cmd}')
        
        # Show first few commands for verification
        print('📋 Sample commands loaded:')
        for i, cmd in enumerate(sorted(red_commands)[:10]):
            print(f'  🟢 /{cmd}')
        if len(red_commands) > 10:
            print(f'  ... and {len(red_commands) - 10} more')
        
        # Sync slash commands with enhanced logging
        try:
            print('🔄 Syncing slash commands with Discord...')
            start_time = datetime.now()
            synced = await self.tree.sync()
            sync_time = (datetime.now() - start_time).total_seconds()
            
            print(f'✅ Synced {len(synced)} slash commands in {sync_time:.1f}s')
            
            # Verify sync results
            synced_red = [cmd.name for cmd in synced if cmd.name.startswith('red-')]
            synced_other = [cmd.name for cmd in synced if not cmd.name.startswith('red-')]
            
            print(f'� Sync Results:')
            print(f'  🟢 Red-prefixed commands synced: {len(synced_red)}')
            if synced_other:
                print(f'  🔴 Non-red commands synced: {len(synced_other)}')
                for cmd in synced_other:
                    print(f'    - {cmd}')
            
            # Final status
            if len(synced_red) > 0 and len(synced_other) == 0:
                print('🎉 SUCCESS: All synced commands have red- prefix!')
                print('💡 Commands should now appear in Discord. Type /red to test.')
            else:
                print('⚠️ WARNING: Sync completed but may have issues')
                
        except Exception as e:
            print(f'❌ Failed to sync slash commands: {e}')
            import traceback
            traceback.print_exc()
    
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
