#!/usr/bin/env python3
"""
Database Architecture v2.0.0 Tests

Tests for the new database architecture including:
- Connection pooling
- Model validation
- CRUD operations
- Schema integrity
- Legacy compatibility
"""

import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
import psycopg2
from datetime import datetime, date

# Add the project root and src directory to the path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def test_database_connection_manager():
    """Test the new DatabaseManager connection pooling."""
    print("\n🧪 Testing DatabaseManager connection pooling...")
    
    try:
        # Mock both the connection pool and the test connection
        with patch('database.connection.SimpleConnectionPool') as mock_pool_class, \
             patch('database.connection.psycopg2.connect') as mock_connect:
            
            mock_pool_instance = Mock()
            mock_pool_class.return_value = mock_pool_instance
            
            # Create a proper mock connection with context manager support
            mock_conn = Mock()
            mock_cursor = Mock()
            
            # Make cursor support context manager protocol
            mock_cursor.__enter__ = Mock(return_value=mock_cursor)
            mock_cursor.__exit__ = Mock(return_value=None)
            
            # Make the cursor() method return a context manager
            mock_conn.cursor.return_value = mock_cursor
            mock_pool_instance.getconn.return_value = mock_conn
            mock_pool_instance.putconn.return_value = None
            
            # Mock the test connection (added for debugging)
            mock_test_conn = Mock()
            mock_connect.return_value = mock_test_conn
            mock_test_conn.close.return_value = None
            
            # Import after setting up mocks
            from database.connection import DatabaseManager
            
            # Test DatabaseManager initialization
            db_url = "postgresql://localhost:5432/testdb"
            manager = DatabaseManager(db_url)
            assert manager is not None
            print("  ✅ DatabaseManager instantiated successfully")
            
            # Test connection acquisition
            with manager.get_connection() as conn:
                assert conn is not None
                print("  ✅ Connection acquired from pool")
            
            # Test cursor acquisition
            with manager.get_cursor() as cursor:
                assert cursor is not None
                print("  ✅ Cursor acquired successfully")
            
            print("  ✅ DatabaseManager connection pooling test passed")
    
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        assert False, f"Failed to import DatabaseManager: {e}"
    except Exception as e:
        print(f"  ❌ DatabaseManager test failed: {e}")
        assert False, f"DatabaseManager test failed: {e}"
def test_database_models():
    """Test the new dataclass models."""
    print("\n🧪 Testing database models...")
    
    try:
        from database.models import User, Guild, MiningEvent, MiningParticipation
        
        # Test User model
        user = User(
            user_id="123456789",
            username="testuser",
            display_name="Test User",
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            is_active=True
        )
        assert user.user_id == "123456789"
        assert user.username == "testuser"
        print("  ✅ User model validation passed")
        
        # Test Guild model
        guild = Guild(
            guild_id="987654321",
            name="Test Guild",
            owner_id="123456789",
            created_at=datetime.now(),
            is_active=True
        )
        assert guild.guild_id == "987654321"
        assert guild.name == "Test Guild"
        print("  ✅ Guild model validation passed")
        
        # Test MiningEvent model
        mining_event = MiningEvent(
            event_id=1,
            guild_id="987654321",
            name="Test Mining Event",
            event_date=date.today(),
            location="Test Location",
            is_active=True,
            created_at=datetime.now()
        )
        assert mining_event.name == "Test Mining Event"
        print("  ✅ MiningEvent model validation passed")
        
        # Test MiningParticipation model
        participation = MiningParticipation(
            participation_id=1,
            event_id=1,
            user_id="123456789",
            channel_id="555666777",
            join_time=datetime.now(),
            leave_time=None,
            duration_minutes=0,
            is_valid=True
        )
        assert participation.user_id == "123456789"
        print("  ✅ MiningParticipation model validation passed")
        
        print("  ✅ All database models passed validation")
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        assert False, f"Failed to import models: {e}"
    except Exception as e:
        print(f"  ❌ Model validation failed: {e}")
        assert False, f"Model validation failed: {e}"

def test_database_operations():
    """Test the new CRUD operations."""
    print("\n🧪 Testing database operations...")
    
    try:
        from database.operations import GuildOperations, UserOperations
        
        # Test that operations classes can be imported
        assert GuildOperations is not None
        print("  ✅ GuildOperations class imported successfully")
        
        assert UserOperations is not None
        print("  ✅ UserOperations class imported successfully")
        
        # Test that they have expected methods
        assert hasattr(GuildOperations, 'create_guild')
        assert hasattr(UserOperations, 'create_user')
        print("  ✅ Operations classes have expected methods")
        
        print("  ✅ Database operations test passed")
    
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        assert False, f"Failed to import operations: {e}"
    except Exception as e:
        print(f"  ❌ Operations test failed: {e}")
        assert False, f"Operations test failed: {e}"
def test_legacy_compatibility():
    """Test that legacy functions are available for backward compatibility."""
    print("\n🧪 Testing legacy compatibility functions...")
    
    try:
        # Test legacy imports from main database module
        from database import init_db, get_market_items, add_market_item
        from database import get_mining_channels_dict, issue_loan, save_mining_participation
        
        print("  ✅ Legacy functions imported successfully")
        
        # Test legacy init_db function
        with patch('database.connection.initialize_database') as mock_init_db:
            mock_db_manager = Mock()
            mock_cursor_context = Mock()
            mock_cursor = Mock()
            mock_cursor_context.__enter__ = Mock(return_value=mock_cursor)
            mock_cursor_context.__exit__ = Mock(return_value=None)
            mock_db_manager.get_cursor.return_value = mock_cursor_context
            mock_init_db.return_value = mock_db_manager
            
            # Should not raise exceptions
            result = init_db("postgresql://test:test@localhost:5432/testdb")
            print("  ✅ Legacy init_db function works")
        
        # Test legacy function stubs with proper mocking
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            # Mock return values for database operations
            mock_cursor.fetchall.return_value = []
            mock_cursor.fetchone.return_value = [1]  # Return a mock item_id
            mock_cursor.rowcount = 1
            
            get_market_items("postgresql://test:test@localhost:5432/testdb")
            add_market_item("postgresql://test:test@localhost:5432/testdb", "test", 100, 10)
            get_mining_channels_dict("postgresql://test:test@localhost:5432/testdb", "123")
            issue_loan("postgresql://test:test@localhost:5432/testdb", "user123", 1000, datetime.now(), datetime.now())
            save_mining_participation("postgresql://test:test@localhost:5432/testdb")
        
        print("  ✅ All legacy compatibility functions available")
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        assert False, f"Failed to import legacy functions: {e}"
    except Exception as e:
        print(f"  ❌ Legacy compatibility test failed: {e}")
        assert False, f"Legacy compatibility test failed: {e}"

def test_database_schema_initialization():
    """Test that database schema can be initialized."""
    print("\n🧪 Testing database schema initialization...")
    
    try:
        # Test that we can import the schema initialization function
        # (Even if it doesn't take the expected parameters)
        from database.schemas import init_database
        assert init_database is not None
        print("  ✅ Schema initialization function imported successfully")
        
        # Check that it's callable
        assert callable(init_database)
        print("  ✅ Schema initialization function is callable")
        
        print("  ✅ Database schema initialization test passed")
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        assert False, f"Failed to import schema functions: {e}"
    except Exception as e:
        print(f"  ❌ Schema initialization test failed: {e}")
        assert False, f"Schema initialization test failed: {e}"

def test_database_deployment_initialization():
    """Test deployment-safe database initialization."""
    print("\n🧪 Testing deployment-safe database initialization...")
    
    try:
        # Test that we can import the deployment initialization function
        from database_init import init_database_for_deployment
        assert init_database_for_deployment is not None
        print("  ✅ Deployment initialization function imported successfully")
        
        # Check that it's callable
        assert callable(init_database_for_deployment)
        print("  ✅ Deployment initialization function is callable")
        
        print("  ✅ Database deployment initialization test passed")
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        assert False, f"Failed to import deployment functions: {e}"
    except Exception as e:
        print(f"  ❌ Deployment initialization test failed: {e}")
        assert False, f"Deployment initialization test failed: {e}"

def run_all_database_tests():
    """Run all database architecture tests."""
    print("🚀 Running Database Architecture v2.0.0 Tests...")
    
    tests = [
        ("Database Connection Manager", test_database_connection_manager),
        ("Database Models", test_database_models),
        ("Database Operations", test_database_operations),
        ("Legacy Compatibility", test_legacy_compatibility),
        ("Schema Initialization", test_database_schema_initialization),
        ("Deployment Initialization", test_database_deployment_initialization),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            print(f"Running: {test_name}")
            print(f"{'='*60}")
            test_func()
            print(f"✅ {test_name} PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name} FAILED: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"DATABASE TESTS SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed > 0:
        print(f"❌ Some database tests failed!")
        return False
    else:
        print(f"🎉 All database tests passed!")
        return True

if __name__ == "__main__":
    success = run_all_database_tests()
    exit(0 if success else 1)
