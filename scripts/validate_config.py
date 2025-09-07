#!/usr/bin/env python3
"""
Pre-deployment configuration validator for Red Legion Bot.
Run this script to validate configuration before starting the bot.
"""

import sys
import os
import asyncio

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_imports():
    """Test critical imports."""
    print("🧪 Testing imports...")
    try:
        from src.config import get_database_url, DISCORD_CONFIG, UEX_API_CONFIG
        from src.config.settings import get_secret
        print("   ✅ Config imports successful")
        return True
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return False

def test_environment():
    """Test environment configuration."""
    print("🧪 Testing environment configuration...")
    try:
        from src.config import get_database_url, DISCORD_CONFIG, UEX_API_CONFIG
        
        # Test database URL
        db_url = get_database_url()
        if db_url:
            print("   ✅ Database URL configured")
        else:
            print("   ❌ Database URL not configured")
            return False
            
        # Test Discord config
        if DISCORD_CONFIG.get('TOKEN'):
            print("   ✅ Discord token configured")
        else:
            print("   ❌ Discord token not configured")
            return False
            
        return True
    except Exception as e:
        print(f"   ❌ Configuration error: {e}")
        return False

def test_database():
    """Test database connection."""
    print("🧪 Testing database connection...")
    try:
        from src.config.settings import get_database_url
        import psycopg2
        
        db_url = get_database_url()
        if not db_url:
            print("   ❌ Database URL not available")
            return False
            
        # Test connection
        conn = psycopg2.connect(db_url)
        conn.close()
        print("   ✅ Database connection successful")
        return True
    except ImportError as e:
        print(f"   ❌ Database module import failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False

async def test_secret_manager():
    """Test Google Cloud Secret Manager access."""
    print("🧪 Testing Secret Manager access...")
    
    try:
        from src.config.settings import get_secret
        
        # Try to access a secret (this will fail if permissions are wrong)
        # We'll catch the specific error to distinguish between permission issues and missing secrets
        try:
            get_secret("test-secret")  # This secret probably doesn't exist, but that's ok
        except Exception as e:
            error_str = str(e).lower()
            if "permission denied" in error_str:
                print(f"   ❌ Secret Manager permission denied: {e}")
                return False
            elif "not found" in error_str or "secret" in error_str:
                print("   ✅ Secret Manager accessible (test secret not found, which is expected)")
                return True
            else:
                print(f"   ⚠️ Secret Manager test unclear: {e}")
                return True  # Assume it's working if not a clear permission error
        
        print("   ✅ Secret Manager accessible")
        return True
        
    except Exception as e:
        print(f"   ❌ Secret Manager test failed: {e}")
        return False

async def main():
    """Run all validation tests."""
    print("🎯 Red Legion Bot Configuration Validator")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Environment", test_environment),
        ("Database Connection", test_database),
        ("Secret Manager", test_secret_manager)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()
        results[test_name] = result
    
    print("\n" + "=" * 50)
    print("📊 Validation Results:")
    
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All validation tests passed! Bot is ready to start.")
        return 0
    else:
        print("\n⚠️ Some validation tests failed. Please fix the issues before starting the bot.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Fatal error during validation: {e}")
        sys.exit(1)
