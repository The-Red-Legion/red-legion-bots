#!/usr/bin/env python3
"""
Quick script to check event payroll calculation status
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from database.connection import get_cursor

try:
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT event_id, event_name, status, payroll_calculated, payroll_calculated_at 
            FROM events 
            WHERE event_type = 'mining' 
            ORDER BY ended_at DESC 
            LIMIT 5
        """)
        
        results = cursor.fetchall()
        print("📊 Recent Mining Events:")
        print("=" * 70)
        
        for row in results:
            print(f"Event: {row['event_id']} - {row['event_name']}")
            print(f"  Status: {row['status']}")
            print(f"  Payroll Calculated: {row['payroll_calculated']}")
            print(f"  Calculated At: {row['payroll_calculated_at']}")
            print()
            
        # Also check payroll sessions
        print("\n🔄 Active Payroll Sessions:")
        print("=" * 70)
        cursor.execute("""
            SELECT session_id, event_id, current_step, is_completed, created_at
            FROM payroll_sessions 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        sessions = cursor.fetchall()
        for session in sessions:
            print(f"Session: {session['session_id']}")
            print(f"  Event: {session['event_id']}")
            print(f"  Step: {session['current_step']}")
            print(f"  Completed: {session['is_completed']}")
            print(f"  Created: {session['created_at']}")
            print()
            
except Exception as e:
    print(f"Error: {e}")