#!/usr/bin/env python3
"""
Database Architecture Test

Test script to validate the new Red Legion Bot database architecture.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_imports():
    """Test that all database components can be imported."""
    print("🧪 Testing database imports...")
    
    try:
        # Test connection imports
        from database.connection import DatabaseManager, get_connection, initialize_database
        print("  ✅ Connection module imported")
        
        # Test model imports
        from database.models import Guild, User, MiningEvent, EventStatus
        print("  ✅ Models imported")
        
        # Test operations imports
        from database.operations import GuildOperations, UserOperations
        print("  ✅ Operations imported")
        
        # Test schema imports
        from database.schemas import init_database, SchemaManager
        print("  ✅ Schema module imported")
        
        # Test main database module
        from database import DATABASE_VERSION
        print(f"  ✅ Database module imported (version {DATABASE_VERSION})")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False

def test_model_creation():
    """Test creating model instances."""
    print("\n🧪 Testing model creation...")
    
    try:
        from database.models import Guild, User, MiningEvent, EventStatus
        from datetime import datetime, date
        
        # Test Guild model
        guild = Guild(
            id=123456789,
            name="Red Legion Test",
            settings={"test": True}
        )
        print(f"  ✅ Guild created: {guild.name}")
        
        # Test User model  
        user = User(
            id=987654321,
            username="test_user",
            display_name="Test User"
        )
        print(f"  ✅ User created: {user.username}")
        
        # Test MiningEvent model
        event = MiningEvent(
            guild_id=guild.id,
            event_date=date.today(),
            event_time=datetime.now(),
            status=EventStatus.PLANNED
        )
        print(f"  ✅ Mining event created: {event.event_name}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Model creation failed: {e}")
        return False

def test_schema_structure():
    """Test schema definitions."""
    print("\n🧪 Testing schema structure...")
    
    try:
        from database.schemas.core import COMPLETE_SCHEMA, SCHEMA_VERSION
        
        print(f"  ✅ Schema version: {SCHEMA_VERSION}")
        print(f"  ✅ Schema sections: {len(COMPLETE_SCHEMA)}")
        
        # Validate schema sections contain required tables
        schema_text = "\n".join(COMPLETE_SCHEMA)
        required_tables = [
            'guilds',
            'users',
            'guild_memberships', 
            'mining_events',
            'mining_channels',
            'mining_participation',
            'materials',
            'mining_yields',
            'loans'
        ]
        
        for table in required_tables:
            if f"CREATE TABLE IF NOT EXISTS {table}" in schema_text:
                print(f"    ✅ {table} table defined")
            else:
                print(f"    ❌ {table} table missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Schema test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Red Legion Bot - Database Architecture Test")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Model Creation Test", test_model_creation), 
        ("Schema Structure Test", test_schema_structure),
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        if test_func():
            print(f"✅ {test_name} PASSED")
            passed += 1
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n{'='*50}")
    print(f"🏁 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Database architecture is ready.")
        print("\n📋 Next Steps:")
        print("1. Initialize database with real connection")
        print("2. Create additional operation classes (mining, economy)")
        print("3. Add comprehensive unit tests")
        print("4. Integrate with Discord bot commands")
        return True
    else:
        print("❌ Some tests failed. Please fix issues before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
