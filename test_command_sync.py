#!/usr/bin/env python3
"""
Test script to check command registration and sync status.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.append('src')

async def test_command_loading():
    """Test loading all command modules and check their commands."""
    print("🔍 Testing Red Legion Command Loading...")
    
    try:
        # Import bot class
        from bot.client import RedLegionBot
        
        # Create bot instance (but don't start it)
        bot = RedLegionBot()
        
        # Load extensions manually to test
        extensions = [
            'commands.diagnostics',      # red-health, red-test, red-dbtest, red-config
            'commands.general',          # red-ping
            'commands.market',           # red-market-list, red-market-add
            'commands.admin',            # red-config-refresh, red-restart, etc.
            'commands.loans',            # red-loan-request, red-loan-status
            'commands.events',           # red-events group commands
            'commands.mining.core',      # red-sunday-mining-*, red-payroll
        ]
        
        print("📦 Loading command extensions...")
        loaded_commands = []
        
        for extension in extensions:
            try:
                await bot.load_extension(extension)
                print(f"  ✅ Loaded {extension}")
                
                # Check what commands were added
                for command in bot.tree.get_commands():
                    if hasattr(command, 'name'):
                        loaded_commands.append(command.name)
                        
            except Exception as e:
                print(f"  ❌ Failed to load {extension}: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n🎯 Total commands loaded: {len(loaded_commands)}")
        print("📋 Command list:")
        for cmd in sorted(set(loaded_commands)):
            prefix = "🟢" if cmd.startswith("red-") else "🔴"
            print(f"  {prefix} {cmd}")
            
        # Check for red- prefix commands
        red_commands = [cmd for cmd in loaded_commands if cmd.startswith("red-")]
        other_commands = [cmd for cmd in loaded_commands if not cmd.startswith("red-")]
        
        print(f"\n✅ Commands with 'red-' prefix: {len(red_commands)}")
        print(f"❌ Commands without 'red-' prefix: {len(other_commands)}")
        
        if other_commands:
            print("⚠️ Commands without red- prefix found:")
            for cmd in other_commands:
                print(f"   - {cmd}")
        
        return len(red_commands) > 0
        
    except Exception as e:
        print(f"❌ Error testing command loading: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_command_loading())
    if result:
        print("\n🎉 Command loading test PASSED - red- prefix commands found!")
    else:
        print("\n💥 Command loading test FAILED - no red- prefix commands found!")
