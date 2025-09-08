#!/usr/bin/env python3
"""
Script to verify if a mining event was created in the database
"""

import sys
import os
from datetime import datetime, date

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def verify_mining_event(session_id=None, event_date=None):
    """Verify if mining events exist in the database"""
    
    try:
        from config.settings import get_database_url
        import psycopg2
        from urllib.parse import urlparse
        
        db_url = get_database_url()
        if not db_url:
            print("❌ No database URL available")
            return
        
        print(f"🔍 Connecting to database...")
        print(f"Session ID to verify: {session_id}")
        print(f"Event date: {event_date}")
        print()
        
        # Connect to database with proxy fallback
        parsed = urlparse(db_url)
        if parsed.hostname not in ['127.0.0.1', 'localhost']:
            proxy_url = db_url.replace(f'{parsed.hostname}:{parsed.port}', '127.0.0.1:5433')
            try:
                conn = psycopg2.connect(proxy_url)
                print("✅ Connected via proxy")
            except psycopg2.OperationalError:
                conn = psycopg2.connect(db_url)
                print("✅ Connected directly")
        else:
            conn = psycopg2.connect(db_url)
            print("✅ Connected to local database")
        
        cursor = conn.cursor()
        
        # Check if mining_events table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'mining_events'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("❌ mining_events table does not exist")
            conn.close()
            return
        
        print("✅ mining_events table exists")
        print()
        
        # Get all mining events for today or specified date
        search_date = event_date if event_date else date.today()
        
        print(f"🔍 Searching for mining events on {search_date}...")
        cursor.execute("""
            SELECT id, guild_id, event_date, event_time, event_name, status,
                   total_participants, total_value_auec, payroll_processed, pdf_generated,
                   created_at, updated_at
            FROM mining_events 
            WHERE event_date = %s
            ORDER BY event_time DESC
        """, (search_date,))
        
        events = cursor.fetchall()
        
        if not events:
            print(f"❌ No mining events found for {search_date}")
            
            # Check for events in the last 7 days
            print("\n🔍 Checking events in the last 7 days...")
            cursor.execute("""
                SELECT id, guild_id, event_date, event_time, event_name, status,
                       total_participants, total_value_auec, payroll_processed, pdf_generated,
                       created_at, updated_at
                FROM mining_events 
                WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY event_time DESC
            """)
            
            recent_events = cursor.fetchall()
            if recent_events:
                print(f"Found {len(recent_events)} events in the last 7 days:")
                for event in recent_events:
                    print(f"  Event {event[0]}: {event[4]} on {event[2]} at {event[3]} (Status: {event[5]})")
            else:
                print("❌ No mining events found in the last 7 days")
        else:
            print(f"✅ Found {len(events)} mining events for {search_date}:")
            print()
            
            for event in events:
                event_id, guild_id, event_date, event_time, event_name, status = event[:6]
                total_participants, total_value_auec, payroll_processed, pdf_generated = event[6:10]
                created_at, updated_at = event[10:12]
                
                print(f"📋 Event ID: {event_id}")
                print(f"   Guild ID: {guild_id}")
                print(f"   Event Date: {event_date}")
                print(f"   Event Time: {event_time}")
                print(f"   Event Name: {event_name}")
                print(f"   Status: {status}")
                print(f"   Participants: {total_participants}")
                print(f"   Value (aUEC): {total_value_auec}")
                print(f"   Payroll Processed: {payroll_processed}")
                print(f"   PDF Generated: {pdf_generated}")
                print(f"   Created At: {created_at}")
                print(f"   Updated At: {updated_at}")
                print()
                
                # Check if this could be our session
                if session_id:
                    # Extract date/time from session ID: sunday_20250908_155844
                    try:
                        parts = session_id.split('_')
                        if len(parts) >= 3:
                            session_date_str = parts[1]  # 20250908
                            session_time_str = parts[2]  # 155844
                            
                            # Parse session date
                            session_year = int(session_date_str[:4])
                            session_month = int(session_date_str[4:6])
                            session_day = int(session_date_str[6:8])
                            session_date = date(session_year, session_month, session_day)
                            
                            # Parse session time
                            session_hour = int(session_time_str[:2])
                            session_minute = int(session_time_str[2:4])
                            session_second = int(session_time_str[4:6])
                            
                            # Check if this event matches our session timing
                            if (event_date == session_date and 
                                abs((event_time.hour * 3600 + event_time.minute * 60 + event_time.second) - 
                                    (session_hour * 3600 + session_minute * 60 + session_second)) < 300):  # Within 5 minutes
                                print(f"🎯 This event likely corresponds to session {session_id}")
                                print(f"   Session expected time: {session_hour:02d}:{session_minute:02d}:{session_second:02d}")
                                print(f"   Event actual time: {event_time.strftime('%H:%M:%S')}")
                                print()
                    except Exception as e:
                        print(f"Could not parse session ID for comparison: {e}")
        
        # Check for any participation records
        print("🔍 Checking for participation records...")
        cursor.execute("""
            SELECT COUNT(*) FROM mining_participation 
            WHERE event_id IN (
                SELECT id FROM mining_events WHERE event_date = %s
            )
        """, (search_date,))
        
        participation_count = cursor.fetchone()[0]
        print(f"📊 Found {participation_count} participation records for events on {search_date}")
        
        conn.close()
        print("\n✅ Database verification complete")
        
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    # Parse command line arguments
    session_id = None
    event_date = None
    
    if len(sys.argv) > 1:
        session_id = sys.argv[1]
        
        # Try to extract date from session ID
        try:
            parts = session_id.split('_')
            if len(parts) >= 2:
                date_str = parts[1]  # 20250908
                year = int(date_str[:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                event_date = date(year, month, day)
        except:
            pass
    
    if len(sys.argv) > 2:
        # Manual date override
        try:
            event_date = datetime.strptime(sys.argv[2], '%Y-%m-%d').date()
        except:
            print("Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)
    
    verify_mining_event(session_id, event_date)
