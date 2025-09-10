#!/usr/bin/env python3
"""
Simple test to check database operations without requiring live connection
"""

import sys
import os
from datetime import datetime, date

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_database_operations():
    """Test the database operations functions"""
    
    print("=== Testing Database Operations ===")
    print()
    
    try:
        from config.settings import get_database_url
        from database.operations import create_mining_event, get_mining_events, get_open_mining_events
        
        db_url = get_database_url()
        print(f"Database URL available: {db_url is not None}")
        if db_url:
            # Mask sensitive parts of URL for display
            masked_url = db_url[:20] + "***" + db_url[-20:] if len(db_url) > 40 else "***"
            print(f"Database URL (masked): {masked_url}")
        print()
        
        # Test the function imports
        print("✅ Successfully imported database operation functions:")
        print(f"  - create_mining_event: {create_mining_event}")
        print(f"  - get_mining_events: {get_mining_events}")
        print(f"  - get_open_mining_events: {get_open_mining_events}")
        print()
        
        # Check if these are the stub functions or real implementations
        import inspect
        
        create_event_source = inspect.getsource(create_mining_event)
        if "Legacy function" in create_event_source and "return None" in create_event_source:
            print("❌ create_mining_event is still a stub function")
        else:
            print("✅ create_mining_event has a real implementation")
            
        get_events_source = inspect.getsource(get_mining_events)
        if "Legacy function" in get_events_source and "return []" in get_events_source:
            print("❌ get_mining_events is still a stub function")
        else:
            print("✅ get_mining_events has a real implementation")
            
        print()
        
        # Test what would happen if we called these functions
        print("=== Testing Function Behavior (Dry Run) ===")
        
        test_guild_id = 814699481912049704  # Red Legion guild ID
        test_date = date(2025, 9, 8)
        test_event_name = "Sunday Mining - 2025-09-08"
        
        print(f"Test parameters:")
        print(f"  Guild ID: {test_guild_id}")
        print(f"  Event Date: {test_date}")
        print(f"  Event Name: {test_event_name}")
        print()
        
        if db_url:
            print("⚠️ Database URL is available but connection may fail in deployment environment")
            print("This could explain why events aren't being created in Discord")
            print()
            print("Possible issues:")
            print("1. Database connection timeout in production")
            print("2. Network routing issues between bot and database")
            print("3. Database server not accessible from bot's network")
            print("4. Missing database proxy or connection pooling")
        else:
            print("❌ No database URL - events definitely won't be created")
            
        print()
        print("=== Session ID Analysis ===")
        session_id = "sunday_20250908_155844"
        print(f"Session ID: {session_id}")
        
        # Parse the session ID
        try:
            parts = session_id.split('_')
            date_part = parts[1]  # 20250908
            time_part = parts[2]  # 155844
            
            # Extract date
            year = int(date_part[:4])
            month = int(date_part[4:6])
            day = int(date_part[6:8])
            session_date = date(year, month, day)
            
            # Extract time
            hour = int(time_part[:2])
            minute = int(time_part[2:4])
            second = int(time_part[4:6])
            
            print(f"Parsed session date: {session_date}")
            print(f"Parsed session time: {hour:02d}:{minute:02d}:{second:02d}")
            print(f"This corresponds to: {datetime(year, month, day, hour, minute, second)}")
            
            # This would be the expected event name
            expected_event_name = f"Sunday Mining - {session_date}"
            print(f"Expected event name: {expected_event_name}")
            
        except Exception as e:
            print(f"Error parsing session ID: {e}")
            
    except ImportError as e:
        print(f"❌ Error importing modules: {e}")
    except Exception as e:
        print(f"❌ Error in test: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_database_operations()
