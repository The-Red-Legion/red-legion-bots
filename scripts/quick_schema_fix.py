#!/usr/bin/env python3
"""
Simple Database Schema Fix
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def main():
    print('🔧 Updating database schema...')
    
    try:
        # Import database operations
        from database.operations import init_db
        from config.settings import get_database_url
        
        database_url = get_database_url()
        print('✅ Database URL loaded')
        
        # Initialize/update database with latest schema
        init_db(database_url)
        print('✅ Database schema updated successfully!')
        
        print('🎉 Schema fix complete - guild_id column should now exist')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
