#!/usr/bin/env python3
"""
Test script for the modular command registration system.

This script tests that all command modules can be imported and registered
without actually starting the Discord bot.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_command_imports():
    """Test that all command modules can be imported."""
    print("🧪 Testing command module imports...")
    
    try:
        # Test individual command module imports
        print("  📦 Testing market module...")
        from src.commands import market
        print("  ✅ Market module imported successfully")
        
        print("  💰 Testing loans module...")
        from src.commands import loans
        print("  ✅ Loans module imported successfully")
        
        print("  🎯 Testing events module...")
        from src.commands import events
        print("  ✅ Events module imported successfully")
        
        print("  ⛏️ Testing mining module...")
        from src.commands import mining
        print("  ✅ Mining module imported successfully")
        
        print("  🔍 Testing diagnostics module...")
        from src.commands import diagnostics
        print("  ✅ Diagnostics module imported successfully")
        
        print("  🛡️ Testing admin module...")
        from src.commands import admin
        print("  ✅ Admin module imported successfully")
        
        print("  🏓 Testing general module...")
        from src.commands import general
        print("  ✅ General module imported successfully")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        return False


def test_command_registration():
    """Test the command registration system."""
    print("\n🧪 Testing command registration system...")
    
    try:
        # Import the registration function
        print("  📋 Testing commands.__init__ import...")
        from src.commands import register_all_commands
        print("  ✅ Command registration function imported successfully")
        
        # Test that the function exists and is callable
        if callable(register_all_commands):
            print("  ✅ register_all_commands is callable")
        else:
            print("  ❌ register_all_commands is not callable")
            return False
            
        return True
        
    except Exception as e:
        print(f"  ❌ Registration test failed: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        return False


def test_core_modules():
    """Test core module imports."""
    print("\n🧪 Testing core module imports...")
    
    try:
        print("  🏗️ Testing bot_setup module...")
        from src.core import bot_setup
        print("  ✅ Bot setup module imported successfully")
        
        print("  🎯 Testing decorators module...")
        from src.core import decorators
        print("  ✅ Decorators module imported successfully")
        
        print("  🔧 Testing core functions...")
        if hasattr(bot_setup, 'create_bot_instance'):
            print("  ✅ create_bot_instance function found")
        else:
            print("  ❌ create_bot_instance function not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"  ❌ Core module test failed: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        return False


def test_handler_modules():
    """Test handler module imports."""
    print("\n🧪 Testing handler module imports...")
    
    try:
        print("  🎙️ Testing voice_tracking module...")
        from src.handlers import voice_tracking
        print("  ✅ Voice tracking module imported successfully")
        
        print("  🏠 Testing core handlers module...")
        from src.handlers import core
        print("  ✅ Core handlers module imported successfully")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Handler module test failed: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        return False


def main():
    """Run all tests."""
    print("🚀 Starting modular command system tests...\n")
    
    tests = [
        ("Command Imports", test_command_imports),
        ("Command Registration", test_command_registration),
        ("Core Modules", test_core_modules),
        ("Handler Modules", test_handler_modules),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"{'='*50}")
        print(f"Running: {test_name}")
        print(f"{'='*50}")
        
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Print summary
    print(f"\n{'='*50}")
    print("🏁 TEST SUMMARY")
    print(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Modular system is ready.")
        return 0
    else:
        print(f"⚠️ {total - passed} tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
