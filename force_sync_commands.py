#!/usr/bin/env python3
"""
Script to force sync slash commands and clear old cached commands.
"""

import discord
import asyncio
import sys
from pathlib import Path
import os

# Add src to path for imports
sys.path.append('src')

async def force_sync_commands():
    """Force sync commands to Discord, clearing old cache."""
    print("🔄 Starting forced command sync...")
    
    try:
        # Get bot token
        token = os.environ.get('DISCORD_BOT_TOKEN')
        if not token:
            print("❌ No DISCORD_BOT_TOKEN environment variable found")
            print("Please set your Discord bot token:")
            print("export DISCORD_BOT_TOKEN='your_token_here'")
            return False
        
        # Import bot
        from bot.client import RedLegionBot
        
        # Create bot instance
        bot = RedLegionBot()
        
        @bot.event
        async def on_ready():
            print(f'🤖 Bot connected as {bot.user}')
            print(f'🔗 Connected to {len(bot.guilds)} guild(s)')
            
            # Get current commands before sync
            current_commands = await bot.tree.fetch_commands()
            print(f"📋 Current Discord commands: {len(current_commands)}")
            
            for cmd in current_commands:
                prefix = "🟢" if cmd.name.startswith("red-") else "🔴"
                print(f"  {prefix} {cmd.name}")
            
            # Clear all commands first (this removes old cached commands)
            print("\n🗑️ Clearing all existing commands...")
            bot.tree.clear_commands()
            await bot.tree.sync()
            print("✅ All commands cleared from Discord")
            
            # Load our new extensions
            print("\n📦 Loading new command extensions...")
            await bot.setup_hook()
            
            # Force sync new commands
            print("\n🔄 Syncing new commands...")
            synced = await bot.tree.sync()
            print(f"✅ Synced {len(synced)} new commands")
            
            # Show what was synced
            print("📋 Newly synced commands:")
            for cmd in synced:
                prefix = "🟢" if cmd.name.startswith("red-") else "🔴"
                print(f"  {prefix} {cmd.name}")
            
            print("\n🎉 Command sync complete!")
            print("⏰ Discord may take a few minutes to update commands globally")
            print("💡 Try using /red-ping to test if commands are working")
            
            await bot.close()
        
        # Start bot briefly to sync commands
        await bot.start(token)
        
    except Exception as e:
        print(f"❌ Error during command sync: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Red Legion Command Sync Tool")
    print("This will clear old commands and sync new red- prefix commands")
    print()
    
    response = input("Continue? (y/N): ").lower()
    if response == 'y':
        asyncio.run(force_sync_commands())
    else:
        print("❌ Sync cancelled")
