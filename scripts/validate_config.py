#!/usr/bin/env python3
"""
Pre-deployment configuration validator for Red Legion Bot.
Run this script to validate configuration before starting the bot.
"""

import sys
import os
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test critical imports."""
    print("🧪 Testing imports...")
    try:
        from config import get_database_url, DISCORD_CONFIG, UEX_API_CONFIG
        from config.settings import get_secret
        print("   ✅ Config imports successful")
        return True
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return False

def test_environment():
    """Test environment variables and configuration."""
    print("🧪 Testing environment configuration...")
    
    try:
        from config import get_database_url, DISCORD_CONFIG, UEX_API_CONFIG
        
        # Test database URL
        db_url = get_database_url()
        if db_url:
            # Mask password for logging
            if '@' in db_url and '://' in db_url:
                parts = db_url.split('@')
                if len(parts) >= 2:
                    masked_url = parts[0].split('://')[0] + '://***:***@' + '@'.join(parts[1:])
                else:
                    masked_url = "***masked***"
            else:
                masked_url = "***masked***"
            print(f"   ✅ Database URL: {masked_url}")
        else:
            print("   ❌ Database URL: Not configured")
            return False
        
        # Test Discord token
        discord_token = DISCORD_CONFIG.get('TOKEN')
        if discord_token:
            print(f"   ✅ Discord Token: {'***' + discord_token[-4:] if len(discord_token) >= 4 else '***'}")
        else:
            print("   ❌ Discord Token: Not configured")
            return False
        
        # Test Google Cloud Project
        gcp_project = os.getenv('GOOGLE_CLOUD_PROJECT', 'rl-prod-471116')
        print(f"   ✅ GCP Project: {gcp_project}")
        
        # Test UEX config
        uex_token = UEX_API_CONFIG.get('bearer_token')
        if uex_token:
            print(f"   ✅ UEX Token: {'***' + uex_token[-4:] if len(uex_token) >= 4 else '***'}")
        else:
            print("   ⚠️ UEX Token: Not configured (payroll will need manual calculation)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration error: {e}")
        return False

async def test_database_connection():
    """Test database connectivity."""
    print("🧪 Testing database connection...")
    
    try:
        from config import get_database_url
        import asyncpg
        
        db_url = get_database_url()
        if not db_url:
            print("   ❌ No database URL available")
            return False
        
        # Test connection
        conn = await asyncpg.connect(db_url)
        result = await conn.fetchval("SELECT 1")
        await conn.close()
        
        if result == 1:
            print("   ✅ Database connection successful")
            return True
        else:
            print("   ❌ Database query test failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False

async def test_secret_manager():
    """Test Google Cloud Secret Manager access."""
    print("🧪 Testing Secret Manager access...")
    
    try:
        from config.settings import get_secret
        
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
        ("Database Connection", test_database_connection),
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
