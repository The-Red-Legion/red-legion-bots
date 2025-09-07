#!/usr/bin/env python3
"""
Comprehensive validation test for the Red Legion Discord bot.

This test validates that the main bot file can be imported and 
all critical functions are available without actually starting Discord.
"""

import sys
import os
from unittest.mock import Mock, patch

# Add the project root and src directory to the path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))


def test_main_bot_syntax():
    """Test main bot file syntax."""
    print("\n🧪 Testing main bot file syntax...")
    
    # Test both the new main.py and legacy participation_bot.py
    test_files = ['src/main.py', 'src/participation_bot.py']
    
    for file_path in test_files:
        try:
            if not os.path.exists(file_path):
                print(f"  ⚠️ {file_path} not found (may be expected for reorganized structure)")
                continue
                
            with open(file_path, 'r') as f:
                code = f.read()
            
            compile(code, file_path, 'exec')
            print(f"  ✅ {file_path} syntax is valid")
            
        except SyntaxError as e:
            print(f"  ❌ Syntax error in {file_path}: {e}")
            print(f"     Line {e.lineno}: {e.text}")
            return False
        except Exception as e:
            print(f"  ❌ Error reading {file_path}: {e}")
            return False
    
    return True
sys.path.insert(0, os.path.join(project_root, 'src'))

def test_main_bot_file_syntax():
    """Test that the main bot file has valid syntax."""
    print("🧪 Testing main bot file syntax...")
    
    try:
        # Test that we can compile the file
        with open('src/participation_bot.py', 'r') as f:
            code = f.read()
        
        compile(code, 'src/participation_bot.py', 'exec')
        print("  ✅ Main bot file syntax is valid")
        return True
        
    except SyntaxError as e:
        print(f"  ❌ Syntax error in main bot file: {e}")
        print(f"     Line {e.lineno}: {e.text}")
        return False
    except Exception as e:
        print(f"  ❌ Error reading main bot file: {e}")
        return False


def test_critical_imports():
    """Test critical imports that the bot needs."""
    print("\n🧪 Testing critical imports...")
    
    critical_imports = [
        ('src.config', 'DISCORD_TOKEN, get_database_url'),
        ('src.database', 'init_db'),
        ('src.core.bot_setup', 'create_bot_instance'),
        ('src.commands', 'register_all_commands'),
        ('src.event_handlers', 'setup_event_handlers'),
    ]
    
    all_passed = True
    
    for module_name, items in critical_imports:
        try:
            print(f"  📦 Testing {module_name}...")
            module = __import__(module_name, fromlist=items.split(', '))
            
            for item in items.split(', '):
                if hasattr(module, item):
                    print(f"    ✅ {item}")
                else:
                    print(f"    ❌ {item} - NOT FOUND")
                    all_passed = False
                    
        except Exception as e:
            print(f"    ❌ Failed to import {module_name}: {e}")
            all_passed = False
    
    return all_passed


def test_command_count_validation():
    """Validate that we have the expected number of commands."""
    print("\n🧪 Testing command count validation...")
    
    try:
        from commands import register_all_commands
        
        # Create a simple mock to count commands
        class CommandCounter:
            def __init__(self):
                self.command_count = 0
                self.cog_count = 0
                self.tree = Mock()  # Mock tree for slash commands
                self.tree.command = self.command  # Redirect tree commands to regular commands
                
            def command(self, name=None, **kwargs):
                def decorator(func):
                    self.command_count += 1
                    return func
                return decorator
            
            def add_cog(self, cog):
                """Mock add_cog method for discord.py cogs."""
                self.cog_count += 1
                # Count commands in the cog
                for attr_name in dir(cog):
                    attr = getattr(cog, attr_name)
                    if hasattr(attr, '__discord_commands__'):
                        self.command_count += len(attr.__discord_commands__)
                    elif callable(attr) and hasattr(attr, 'callback'):
                        self.command_count += 1
        
        counter = CommandCounter()
        register_all_commands(counter)
        
        expected_count = 15  # From our test above
        actual_count = counter.command_count
        
        print(f"  📊 Expected commands: {expected_count}")
        print(f"  📊 Actual commands: {actual_count}")
        
        if actual_count == expected_count:
            print("  ✅ Command count matches expected")
            return True
        else:
            print(f"  ❌ Command count mismatch (expected {expected_count}, got {actual_count})")
            return False
            
    except Exception as e:
        print(f"  ❌ Command count validation failed: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        return False


def test_database_function_availability():
    """Test that database functions are available."""
    print("\n🧪 Testing database function availability...")
    
    try:
        from database import init_db
        print("  ✅ init_db function available")
        
        # Test config database URL function
        from config import get_database_url
        print("  ✅ get_database_url function available")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Database function test failed: {e}")
        return False


def test_file_structure():
    """Test that all expected files exist."""
    print("\n🧪 Testing file structure...")
    
    expected_files = [
        'src/main.py',  # New entry point
        'src/participation_bot.py',  # Legacy file (still exists)
        'src/config.py',  # Legacy file (still exists)
        'src/database.py',  # Legacy file (still exists) 
        'src/event_handlers.py',  # Legacy file (still exists)
        
        # New modular structure
        'src/config/__init__.py',
        'src/config/settings.py',
        'src/config/channels.py',
        'src/database/__init__.py',
        'src/database/models.py',
        'src/database/operations.py',
        'src/bot/__init__.py',
        'src/bot/client.py',
        'src/bot/utils.py',
        'src/utils/__init__.py',
        'src/utils/decorators.py',
        'src/utils/discord_helpers.py',
        
        # Core modules
        'src/core/__init__.py',
        'src/core/bot_setup.py',
        'src/core/decorators.py',
        
        # Commands (modular)
        'src/commands/__init__.py',
        'src/commands/market.py',
        'src/commands/loans.py',
        'src/commands/events.py',
        'src/commands/diagnostics.py',
        'src/commands/general.py',
        'src/commands/mining/__init__.py',
        'src/commands/mining/core.py',
        'src/commands/admin/__init__.py',
        'src/commands/admin/core.py',
        
        # Handlers
        'src/handlers/__init__.py',
        'src/handlers/voice_tracking.py',
        'src/handlers/core.py',
    ]
    
    missing_files = []
    
    for file_path in expected_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"  ❌ Missing files: {missing_files}")
        return False
    
    print(f"  ✅ All {len(expected_files)} expected files present")
    return True


def main():
    """Run validation tests."""
    print("🚀 Starting syntax and import validation tests...\n")
    
    tests = [
        ("File Structure", test_file_structure),
        ("Main Bot File Syntax", test_main_bot_file_syntax),
        ("Critical Imports", test_critical_imports),
        ("Command Count Validation", test_command_count_validation),
        ("Database Function Availability", test_database_function_availability),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"{'='*60}")
        print(f"Running: {test_name}")
        print(f"{'='*60}")
        
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Print summary
    print(f"\n{'='*60}")
    print("🏁 VALIDATION TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validation tests passed! The bot is ready to start.")
        print("\n📋 NEXT STEPS:")
        print("1. ✅ Modular structure created")
        print("2. ✅ Command registration system tested")
        print("3. 🔄 Ready for live testing with Discord")
        return 0
    else:
        print(f"⚠️ {total - passed} tests failed. Fix issues before proceeding.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
