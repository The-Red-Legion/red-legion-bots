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
        from database.connection import DatabaseManager
        
        # Test that DatabaseManager can be instantiated
        db_url = "postgresql://test:test@localhost:5432/testdb"
        
        with patch('psycopg2.pool.ThreadedConnectionPool') as mock_pool:
            # Mock the connection pool
            mock_pool_instance = Mock()
            mock_pool.return_value = mock_pool_instance
            
            # Mock connection and cursor
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_pool_instance.getconn.return_value = mock_conn
            
            # Test DatabaseManager initialization
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
        from database.connection import DatabaseManager
        
        # Mock database connection
        with patch('psycopg2.pool.ThreadedConnectionPool') as mock_pool:
            mock_pool_instance = Mock()
            mock_pool.return_value = mock_pool_instance
            
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_pool_instance.getconn.return_value = mock_conn
            
            db_url = "postgresql://test:test@localhost:5432/testdb"
            db_manager = DatabaseManager(db_url)
            
            # Test GuildOperations
            guild_ops = GuildOperations(db_manager)
            assert guild_ops is not None
            print("  ✅ GuildOperations instantiated successfully")
            
            # Test UserOperations
            user_ops = UserOperations(db_manager)
            assert user_ops is not None
            print("  ✅ UserOperations instantiated successfully")
            
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
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            # Should not raise exceptions
            result = init_db("postgresql://test:test@localhost:5432/testdb")
            print("  ✅ Legacy init_db function works")
        
        # Test legacy function stubs (should not raise exceptions)
        get_market_items("test_url")
        add_market_item("test_url", "test", 100, 10)
        get_mining_channels_dict("test_url", "123")
        issue_loan("test_url", "user123", 1000, datetime.now(), datetime.now())
        save_mining_participation("test_url")
        
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
        from database.schemas import init_database
        
        with patch('psycopg2.pool.ThreadedConnectionPool') as mock_pool:
            mock_pool_instance = Mock()
            mock_pool.return_value = mock_pool_instance
            
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_pool_instance.getconn.return_value = mock_conn
            
            # Should not raise exceptions
            result = init_database("postgresql://test:test@localhost:5432/testdb")
            print("  ✅ Database schema initialization completed")
            
            # Verify that SQL was executed
            assert mock_cursor.execute.called
            print("  ✅ SQL schema execution verified")
        
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
        from database_init import init_database_for_deployment
        
        with patch('database.schemas.init_database') as mock_init:
            mock_init.return_value = True
            
            # Test successful initialization
            result = init_database_for_deployment("postgresql://test:test@localhost:5432/testdb")
            assert result is True
            print("  ✅ Deployment initialization succeeded")
            
        with patch('database.schemas.init_database') as mock_init:
            mock_init.side_effect = Exception("Connection failed")
            
            # Test failure handling
            result = init_database_for_deployment("postgresql://test:test@localhost:5432/testdb")
            assert result is False
            print("  ✅ Deployment initialization handles failures gracefully")
        
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
