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
        
        # Load extensions manually to test the new modules architecture
        extensions = [
            'commands.mining',           # Wrapper for mining module (/mining start, /mining stop)
            'commands.payroll',          # Wrapper for payroll module (/payroll mining, /payroll salvage)
            'commands.diagnostics',      # red-health, red-test, red-dbtest
            'commands.general',          # red-ping
            'commands.admin',            # red-restart, red-config-refresh
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
            
        # Check for both module commands and red- prefix commands
        module_commands = [cmd for cmd in loaded_commands if cmd in ['mining', 'payroll']]
        red_commands = [cmd for cmd in loaded_commands if cmd.startswith("red-")]
        other_commands = [cmd for cmd in loaded_commands if not cmd.startswith("red-") and cmd not in ['mining', 'payroll']]
        
        print(f"\n✅ Module commands (mining/payroll): {len(module_commands)}")
        print(f"✅ Commands with 'red-' prefix: {len(red_commands)}")
        print(f"❌ Other commands: {len(other_commands)}")
        
        if other_commands:
            print("⚠️ Unexpected commands found:")
            for cmd in other_commands:
                print(f"   - {cmd}")
        
        return len(module_commands) > 0 or len(red_commands) > 0
        
    except Exception as e:
        print(f"❌ Error testing command loading: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_command_loading())
    if result:
        print("\n🎉 Command loading test PASSED - module commands or red- prefix commands found!")
    else:
        print("\n💥 Command loading test FAILED - no valid commands found!")
