#!/usr/bin/env python3
"""
Database Performance Tests

Tests to ensure the new database architecture v2.0.0 performs well
and doesn't have obvious bottlenecks or memory leaks.
"""

import sys
import os
import time
from unittest.mock import Mock, patch

# Add the project root and src directory to the path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def test_import_performance():
    """Test that database imports are fast."""
    print("\n🧪 Testing database import performance...")
    
    start_time = time.time()
    
    try:
        import database
        import database_init
        from database import connection, models, operations
        
        import_time = time.time() - start_time
        
        # Imports should be fast (under 1 second)
        if import_time > 1.0:
            print(f"  ⚠️ Imports took {import_time:.2f}s (slower than expected)")
            return False
        else:
            print(f"  ✅ All imports completed in {import_time:.3f}s")
            return True
            
    except Exception as e:
        print(f"  ❌ Import performance test failed: {e}")
        return False

def test_legacy_function_performance():
    """Test that legacy functions execute quickly."""
    print("\n🧪 Testing legacy function performance...")
    
    try:
        from database import (
            get_market_items, add_market_item, get_mining_channels_dict,
            issue_loan, save_mining_participation
        )
        
        start_time = time.time()
        
        # Call each function multiple times
        for i in range(100):
            get_market_items("fake_url")
            add_market_item("fake_url", f"item_{i}", 100, 10)
            get_mining_channels_dict("fake_url", f"guild_{i}")
            issue_loan("fake_url", f"user_{i}", 1000, None, None)
            save_mining_participation("fake_url")
        
        execution_time = time.time() - start_time
        
        # 500 function calls should be very fast (under 0.1 seconds)
        if execution_time > 0.1:
            print(f"  ⚠️ 500 legacy function calls took {execution_time:.2f}s (slower than expected)")
            return False
        else:
            print(f"  ✅ 500 legacy function calls completed in {execution_time:.3f}s")
            return True
            
    except Exception as e:
        print(f"  ❌ Legacy function performance test failed: {e}")
        return False

def test_memory_usage():
    """Test that importing database modules doesn't use excessive memory."""
    print("\n🧪 Testing memory usage...")
    
    try:
        import psutil
        import gc
        
        # Get baseline memory
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Import database modules
        import database
        import database_init
        from database import connection, models, operations
        
        # Force garbage collection
        gc.collect()
        
        # Check memory after imports
        after_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = after_memory - baseline_memory
        
        print(f"  📊 Baseline memory: {baseline_memory:.1f} MB")
        print(f"  📊 After imports: {after_memory:.1f} MB")
        print(f"  📊 Memory increase: {memory_increase:.1f} MB")
        
        # Database imports should not use excessive memory (< 50MB increase)
        if memory_increase > 50:
            print(f"  ⚠️ Memory increase of {memory_increase:.1f}MB is higher than expected")
            return False
        else:
            print(f"  ✅ Memory usage is acceptable")
            return True
            
    except ImportError:
        print("  ⚠️ psutil not available, skipping memory test")
        return True
    except Exception as e:
        print(f"  ❌ Memory usage test failed: {e}")
        return False

def test_module_structure_efficiency():
    """Test that the module structure is efficient and doesn't have circular imports."""
    print("\n🧪 Testing module structure efficiency...")
    
    try:
        # Test individual imports to ensure no circular dependencies
        modules_to_test = [
            ('database', 'Main database module'),
            ('database.connection', 'Connection module'),
            ('database.models', 'Models module'),
            ('database.operations', 'Operations module'),
            ('database.schemas', 'Schemas module'),
            ('database_init', 'Deployment init module')
        ]
        
        for module_name, description in modules_to_test:
            start_time = time.time()
            
            try:
                __import__(module_name)
                import_time = time.time() - start_time
                
                if import_time > 0.5:
                    print(f"  ⚠️ {description} import took {import_time:.2f}s (slow)")
                else:
                    print(f"  ✅ {description} imported in {import_time:.3f}s")
                    
            except Exception as e:
                print(f"  ❌ Failed to import {module_name}: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Module structure test failed: {e}")
        return False

def run_performance_tests():
    """Run all database performance tests."""
    print("🚀 Running Database Performance Tests...")
    
    tests = [
        ("Import Performance", test_import_performance),
        ("Legacy Function Performance", test_legacy_function_performance),
        ("Memory Usage", test_memory_usage),
        ("Module Structure Efficiency", test_module_structure_efficiency),
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
    print(f"PERFORMANCE TESTS SUMMARY")
    print(f"{'='*50}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed > 0:
        print(f"❌ Some performance tests failed!")
        return False
    else:
        print(f"🎉 All performance tests passed!")
        return True

if __name__ == "__main__":
    success = run_performance_tests()
    exit(0 if success else 1)
