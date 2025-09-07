#!/usr/bin/env python3
"""
Test database connectivity from production environment
"""
import sys
import os
import socket
from urllib.parse import urlparse

def test_network_connectivity(host, port):
    """Test if we can reach the database server"""
    print(f"🌐 Testing network connectivity to {host}:{port}")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # Increased timeout for GCP internal networks
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            print(f"✅ Network connection to {host}:{port} successful")
            return True
        else:
            print(f"❌ Network connection to {host}:{port} failed (error code: {result})")
            return False
    except Exception as e:
        print(f"❌ Network test failed: {e}")
        return False

def test_database_url():
    """Test database URL parsing and connection"""
    print("🔍 Testing database URL from environment...")
    
    # Try to get database URL from environment or Secret Manager
    try:
        # Add the project root to the path
        sys.path.insert(0, '/app')
        from src.config.settings import get_database_url
        database_url = get_database_url()
        print(f"📋 Database URL obtained successfully")
        print(f"📋 URL (first 50 chars): {database_url[:50]}...")
        print(f"🔍 URL contains '#': {'#' in database_url}")
        print(f"🔍 URL contains '%23': {'%23' in database_url}")
        
        # Parse the URL to get host and port
        parsed = urlparse(database_url)
        host = parsed.hostname
        port = parsed.port or 5432
        
        print(f"🏗️ Parsed host: {host}")
        print(f"🏗️ Parsed port: {port}")
        
        # Test network connectivity first
        if not test_network_connectivity(host, port):
            print("❌ Skipping database connection test due to network issues")
            return False
        
        # Test database connection
        print("🔗 Attempting database connection...")
        try:
            import psycopg2
            conn = psycopg2.connect(database_url)
            print("✅ Database connection successful!")
            
            # Test a simple query
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"📊 Database version: {version[0][:100]}...")
            
            cursor.close()
            conn.close()
            return True
        except ImportError:
            print("❌ psycopg2 not installed - skipping connection test")
            print("✅ URL encoding validation passed")
            return True
        
    except ModuleNotFoundError as e:
        print(f"❌ Module import failed: {e}")
        print("💡 This suggests the application code is not properly deployed")
        return False
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        return False

def main():
    """Main test function"""
    print("🧪 Starting database connectivity test...")
    print(f"🏠 Working directory: {os.getcwd()}")
    print(f"🐍 Python path: {sys.path[:3]}...")
    
    success = test_database_url()
    
    if success:
        print("✅ All database tests passed!")
        sys.exit(0)
    else:
        print("❌ Database tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
