#!/usr/bin/env python3
"""
Advanced test for command registration with mock bot instance.

This test creates a mock Discord bot and tests the actual command registration.
"""

import sys
import os
from unittest.mock import Mock, MagicMock

# Add the project root and src directory to the path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

class MockBot:
    """Mock Discord bot for testing."""
    
    def __init__(self):
        self.commands = {}
        self.listeners = {}
        self.guilds = []
        self.latency = 0.050  # 50ms mock latency
        self.user = Mock()
        self.user.name = "Red Legion Bot (Test)"
        
    def command(self, name=None, **kwargs):
        """Mock command decorator."""
        def decorator(func):
            command_name = name or func.__name__
            self.commands[command_name] = {
                'function': func,
                'kwargs': kwargs
            }
            print(f"    ✅ Registered command: {command_name}")
            return func
        return decorator
    
    def add_listener(self, func, name):
        """Mock listener registration."""
        self.listeners[name] = func
        print(f"    ✅ Registered listener: {name}")


def test_command_registration_with_mock_bot():
    """Test command registration with a mock bot instance."""
    print("🧪 Testing command registration with mock bot...")
    
    try:
        # Create mock bot
        mock_bot = MockBot()
        print("  🤖 Created mock bot instance")
        
        # Import and run command registration
        from commands import register_all_commands
        
        print("  📋 Running command registration...")
        register_all_commands(mock_bot)
        
        # Check that commands were registered
        registered_commands = list(mock_bot.commands.keys())
        print(f"  📊 Total commands registered: {len(registered_commands)}")
        
        expected_commands = [
            # Market commands
            'list_market', 'add_market_item',
            # Loan commands  
            'request_loan',
            # Event commands
            'start_logging', 'stop_logging', 'pick_winner', 'list_open_events',
            # Mining commands
            'log_mining_results',
            # Diagnostic commands
            'health', 'test', 'dbtest', 'config_check',
            # Admin commands
            'refresh_config', 'restart_red_legion_bot',
            # General commands
            'ping'
        ]
        
        print("  🔍 Checking for expected commands...")
        missing_commands = []
        for cmd in expected_commands:
            if cmd in registered_commands:
                print(f"    ✅ {cmd}")
            else:
                print(f"    ❌ {cmd} - MISSING")
                missing_commands.append(cmd)
        
        # Check for unexpected commands
        unexpected_commands = [cmd for cmd in registered_commands if cmd not in expected_commands]
        if unexpected_commands:
            print(f"  ⚠️ Unexpected commands found: {unexpected_commands}")
        
        if missing_commands:
            print(f"  ❌ Missing commands: {missing_commands}")
            return False
        
        print(f"  ✅ All {len(expected_commands)} expected commands registered successfully")
        return True
        
    except Exception as e:
        print(f"  ❌ Command registration test failed: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        return False


def test_decorator_functionality():
    """Test that decorators are working properly."""
    print("\n🧪 Testing decorator functionality...")
    
    try:
        from core.decorators import has_org_role, standard_cooldown, error_handler, admin_only
        
        print("  🎯 Testing has_org_role decorator...")
        decorator = has_org_role()
        if callable(decorator):
            print("    ✅ has_org_role returns callable decorator")
        else:
            print("    ❌ has_org_role does not return callable")
            return False
        
        print("  ⏱️ Testing standard_cooldown decorator...")
        cooldown = standard_cooldown()
        if hasattr(cooldown, '__call__'):
            print("    ✅ standard_cooldown returns callable decorator")
        else:
            print("    ❌ standard_cooldown does not return callable")
            return False
        
        print("  🛡️ Testing admin_only decorator...")
        admin_dec = admin_only()
        if callable(admin_dec):
            print("    ✅ admin_only returns callable decorator")
        else:
            print("    ❌ admin_only does not return callable")
            return False
        
        print("  🔧 Testing error_handler decorator...")
        if callable(error_handler):
            print("    ✅ error_handler is callable")
        else:
            print("    ❌ error_handler is not callable")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Decorator test failed: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        return False


def test_bot_setup_functionality():
    """Test bot setup functionality."""
    print("\n🧪 Testing bot setup functionality...")
    
    try:
        from core.bot_setup import create_bot_instance, setup_heartbeat
        
        print("  🤖 Testing create_bot_instance...")
        # We can't actually create a real bot without Discord.py being available
        # But we can test that the function exists and is callable
        if callable(create_bot_instance):
            print("    ✅ create_bot_instance is callable")
        else:
            print("    ❌ create_bot_instance is not callable")
            return False
        
        print("  💓 Testing setup_heartbeat...")
        if callable(setup_heartbeat):
            print("    ✅ setup_heartbeat is callable")
        else:
            print("    ❌ setup_heartbeat is not callable")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Bot setup test failed: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        return False


def main():
    """Run advanced tests."""
    print("🚀 Starting advanced modular system tests...\n")
    
    tests = [
        ("Command Registration (Mock Bot)", test_command_registration_with_mock_bot),
        ("Decorator Functionality", test_decorator_functionality),
        ("Bot Setup Functionality", test_bot_setup_functionality),
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
    print("🏁 ADVANCED TEST SUMMARY")
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
        print("🎉 All advanced tests passed! Command registration system is fully functional.")
        return 0
    else:
        print(f"⚠️ {total - passed} tests failed. Review the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
