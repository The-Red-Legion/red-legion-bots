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
            try:
                current_commands = await bot.tree.fetch_commands()
                print(f"📋 Current Discord commands: {len(current_commands)}")
                
                old_commands = []
                new_commands = []
                for cmd in current_commands:
                    if cmd.name.startswith("red-"):
                        new_commands.append(cmd.name)
                    else:
                        old_commands.append(cmd.name)
                    print(f"  {'🟢' if cmd.name.startswith('red-') else '🔴'} {cmd.name}")
                
                print(f"\n📊 Command Analysis:")
                print(f"  🟢 Red-prefixed commands: {len(new_commands)}")
                print(f"  🔴 Old commands: {len(old_commands)}")
                
                if old_commands:
                    print(f"\n🗑️ Found {len(old_commands)} old commands to remove:")
                    for cmd in old_commands:
                        print(f"   - {cmd}")
                
            except Exception as e:
                print(f"⚠️ Could not fetch current commands: {e}")
                current_commands = []
            
            # AGGRESSIVE CLEAR: Remove ALL commands first
            print(f"\n🗑️ CLEARING ALL COMMANDS (including old cached ones)...")
            bot.tree.clear_commands()
            
            # Sync the clear (this removes everything from Discord)
            try:
                await bot.tree.sync()
                print("✅ All commands cleared from Discord")
                
                # Wait a moment for Discord to process
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Error clearing commands: {e}")
            
            # Verify commands are cleared
            try:
                cleared_check = await bot.tree.fetch_commands()
                print(f"✅ Verification: {len(cleared_check)} commands remaining (should be 0)")
            except Exception as e:
                print(f"⚠️ Could not verify clear: {e}")
            
            # Load our new extensions
            print(f"\n📦 Loading new command extensions...")
            await bot.setup_hook()
            
            # Check what commands are now loaded locally
            local_commands = [cmd.name for cmd in bot.tree.get_commands() if hasattr(cmd, 'name')]
            print(f"📋 Loaded {len(local_commands)} commands locally:")
            for cmd in sorted(local_commands):
                print(f"  🟢 {cmd}")
            
            # Force sync new commands with guild-specific sync for faster update
            print(f"\n🔄 Syncing new commands (guild-specific for speed)...")
            for guild in bot.guilds:
                try:
                    guild_synced = await bot.tree.sync(guild=guild)
                    print(f"  ✅ Synced {len(guild_synced)} commands to {guild.name}")
                except Exception as e:
                    print(f"  ❌ Failed to sync to {guild.name}: {e}")
            
            # Also do global sync
            print(f"\n🌍 Performing global command sync...")
            try:
                global_synced = await bot.tree.sync()
                print(f"✅ Global sync: {len(global_synced)} commands")
                
                print(f"📋 Globally synced commands:")
                for cmd in global_synced:
                    print(f"  🟢 {cmd.name}")
                    
            except Exception as e:
                print(f"❌ Global sync failed: {e}")
            
            # Final verification
            print(f"\n🔍 Final verification - fetching current Discord commands...")
            try:
                final_commands = await bot.tree.fetch_commands()
                print(f"📋 Discord now shows {len(final_commands)} commands:")
                for cmd in final_commands:
                    prefix = "🟢" if cmd.name.startswith("red-") else "🔴"
                    print(f"  {prefix} {cmd.name}")
                
                red_count = len([cmd for cmd in final_commands if cmd.name.startswith("red-")])
                old_count = len([cmd for cmd in final_commands if not cmd.name.startswith("red-")])
                
                print(f"\n🎯 FINAL RESULT:")
                print(f"  🟢 Red-prefixed commands: {red_count}")
                print(f"  🔴 Old commands remaining: {old_count}")
                
                if old_count == 0 and red_count > 0:
                    print(f"  ✅ SUCCESS: All commands now have red- prefix!")
                else:
                    print(f"  ⚠️ WARNING: Still have old commands or missing red- commands")
                    
            except Exception as e:
                print(f"❌ Could not verify final state: {e}")
            
            print(f"\n🎉 Command sync process complete!")
            print(f"⏰ Discord may take 1-5 minutes to update commands in client")
            print(f"💡 Try refreshing Discord and test with /red-ping")
            
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
