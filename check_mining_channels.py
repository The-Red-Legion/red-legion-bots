#!/usr/bin/env python3
"""
Check mining channels in database and initialize if needed.
"""

import os
import psycopg2
from urllib.parse import urlparse

def get_database_url():
    """Get database URL from file."""
    try:
        with open('db_url.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    return line
    except FileNotFoundError:
        pass
    return None

def parse_db_url(url):
    """Parse database URL into connection parameters."""
    parsed = urlparse(url)
    return {
        'host': parsed.hostname,
        'port': parsed.port,
        'database': parsed.path[1:],  # Remove leading slash
        'user': parsed.username,
        'password': parsed.password
    }

def check_mining_channels():
    """Check what mining channels are in the database."""
    db_url = get_database_url()
    if not db_url:
        print("❌ No database URL found")
        return
    
    print(f"🔍 Using database URL: {db_url[:50]}...")
    
    try:
        conn_params = parse_db_url(db_url)
        print(f"🔌 Connecting to database: {conn_params['host']}:{conn_params['port']}/{conn_params['database']}")
        
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Check if mining_channels table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'mining_channels'
            );
        """)
        table_exists = cursor.fetchone()[0]
        print(f"📋 Mining channels table exists: {table_exists}")
        
        if table_exists:
            # Get all mining channels
            cursor.execute("SELECT channel_id, channel_name, description, is_active FROM mining_channels;")
            channels = cursor.fetchall()
            print(f"📊 Found {len(channels)} mining channels in database:")
            for channel in channels:
                print(f"  - {channel[1]} ({channel[0]}) - {channel[2]} - Active: {channel[3]}")
        else:
            print("❌ Mining channels table does not exist")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    check_mining_channels()
