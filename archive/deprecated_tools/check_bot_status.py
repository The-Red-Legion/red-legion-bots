#!/usr/bin/env python3
"""
Quick check to see what commands the bot currently has loaded.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.append('src')

async def check_bot_status():
    """Check what commands are currently loaded in the bot."""
    print("🔍 Checking Bot Command Status...")
    
    try:
        # Import and create bot
        from bot.client import RedLegionBot
        bot = RedLegionBot()
        
        # Load extensions like the bot normally would
        await bot.setup_hook()
        
        # Get all loaded commands
        commands = bot.tree.get_commands()
        print(f"📦 Bot has {len(commands)} commands loaded locally:")
        
        red_commands = []
        other_commands = []
        
        for cmd in commands:
            if hasattr(cmd, 'name'):
                if cmd.name.startswith('red-'):
                    red_commands.append(cmd.name)
                else:
                    other_commands.append(cmd.name)
        
        print(f"\n✅ Commands with 'red-' prefix ({len(red_commands)}):")
        for cmd in sorted(red_commands):
            print(f"  🟢 /{cmd}")
        
        if other_commands:
            print(f"\n❌ Commands WITHOUT 'red-' prefix ({len(other_commands)}):")
            for cmd in sorted(other_commands):
                print(f"  🔴 /{cmd}")
        else:
            print(f"\n✅ All commands have proper 'red-' prefix!")
        
        # Check for groups
        groups = [cmd for cmd in commands if hasattr(cmd, 'commands')]
        print(f"\n📋 Command groups ({len(groups)}):")
        for group in groups:
            if hasattr(group, 'name'):
                print(f"  📁 /{group.name}")
                if hasattr(group, 'commands'):
                    for subcmd in group.commands:
                        if hasattr(subcmd, 'name'):
                            print(f"    └── {subcmd.name}")
        
        return len(red_commands) > 0 and len(other_commands) == 0
        
    except Exception as e:
        print(f"❌ Error checking bot status: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(check_bot_status())
    print(f"\n{'🎉 Bot configuration looks good!' if result else '⚠️ Bot configuration needs attention'}")
