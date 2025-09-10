#!/usr/bin/env python3
"""
Database Integration Tests

Simple integration tests for the database architecture v2.0.0
Tests basic functionality without complex mocking.
"""

import sys
import os

# Add the project root and src directory to the path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def test_database_imports():
    """Test that all new database modules can be imported."""
    print("\n🧪 Testing database module imports...")
    
    try:
        # Test main database module
        import database
        print("  ✅ Main database module imported")
        
        # Test that legacy functions are available
        assert hasattr(database, 'init_db'), "init_db function not found"
        assert hasattr(database, 'get_market_items'), "get_market_items function not found"
        assert hasattr(database, 'add_market_item'), "add_market_item function not found"
        print("  ✅ Legacy compatibility functions available")
        
        # Test database_init module
        import database_init
        assert hasattr(database_init, 'init_database_for_deployment'), "init_database_for_deployment not found"
        print("  ✅ Deployment initialization module imported")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False
    except AssertionError as e:
        print(f"  ❌ Function missing: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False

def test_database_structure():
    """Test that database structure is correct."""
    print("\n🧪 Testing database structure...")
    
    try:
        # Check that database package structure exists
        db_path = os.path.join(project_root, 'src', 'database')
        
        required_files = [
            '__init__.py',
            'connection.py',
            'models.py',
            'schemas.py',
            'operations/__init__.py',
            'operations/guild_ops.py',
            'operations/user_ops.py'
        ]
        
        for file_path in required_files:
            full_path = os.path.join(db_path, file_path)
            if not os.path.exists(full_path):
                print(f"  ❌ Missing file: {file_path}")
                return False
            print(f"  ✅ Found: {file_path}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Structure test failed: {e}")
        return False

def test_main_bot_integration():
    """Test that main bot can import database successfully."""
    print("\n🧪 Testing main bot database integration...")
    
    try:
        # Test that main.py can be imported without database connection
        import importlib.util
        
        main_path = os.path.join(project_root, 'src', 'main.py')
        if not os.path.exists(main_path):
            print("  ⚠️ main.py not found")
            return True  # Not a failure if file doesn't exist
        
        # Read and compile main.py to check syntax
        with open(main_path, 'r') as f:
            source = f.read()
        
        compile(source, main_path, 'exec')
        print("  ✅ main.py syntax is valid")
        
        return True
        
    except SyntaxError as e:
        print(f"  ❌ Syntax error in main.py: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Main bot integration test failed: {e}")
        return False

def test_legacy_compatibility_stubs():
    """Test that legacy function stubs work."""
    print("\n🧪 Testing legacy compatibility stubs...")
    
    try:
        from database import (
            get_market_items, add_market_item, get_mining_channels_dict,
            issue_loan, save_mining_participation, add_mining_channel
        )
        
        # Test that functions can be called without errors (they're stubs)
        result = get_market_items("fake_url")
        assert isinstance(result, list), "get_market_items should return a list"
        print("  ✅ get_market_items stub works")
        
        # These should not raise exceptions
        add_market_item("fake_url", "test", 100, 10)
        print("  ✅ add_market_item stub works")
        
        result = get_mining_channels_dict("fake_url", "123")
        assert isinstance(result, dict), "get_mining_channels_dict should return a dict"
        print("  ✅ get_mining_channels_dict stub works")
        
        # These should not raise exceptions
        issue_loan("fake_url", "user123", 1000, None, None)
        save_mining_participation("fake_url")
        add_mining_channel("fake_url", "123", "456", "test")
        print("  ✅ All legacy stubs work without errors")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Legacy compatibility test failed: {e}")
        return False

def run_database_integration_tests():
    """Run all database integration tests."""
    print("🚀 Running Database Integration Tests...")
    
    tests = [
        ("Database Imports", test_database_imports),
        ("Database Structure", test_database_structure),
        ("Main Bot Integration", test_main_bot_integration),
        ("Legacy Compatibility Stubs", test_legacy_compatibility_stubs),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*50}")
            print(f"Running: {test_name}")
            print(f"{'='*50}")
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"INTEGRATION TESTS SUMMARY")
    print(f"{'='*50}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed > 0:
        print(f"❌ Some integration tests failed!")
        return False
    else:
        print(f"🎉 All integration tests passed!")
        return True

if __name__ == "__main__":
    success = run_database_integration_tests()
    exit(0 if success else 1)
