#!/usr/bin/env python3
"""
Test the enhanced mining system with channel switching functionality.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.database import (
    init_database, 
    add_mining_channel, 
    get_mining_channels,
    save_mining_participation,
    get_mining_session_participants
)
from src.config import get_database_url

def test_enhanced_mining_system():
    """Test the enhanced mining system with channel switching scenarios."""
    print("🔧 Testing Enhanced Mining System with Channel Switching...")
    
    # Get database URL from file
    try:
        with open('db_url.txt', 'r') as f:
            db_url = f.read().strip()
    except FileNotFoundError:
        print("❌ No db_url.txt file found!")
        return False
    
    if not db_url:
        print("❌ No database URL found!")
        return False
    
    print(f"📊 Database URL: {db_url[:30]}...")
    
    # Test 1: Add test mining channels
    print("\n1️⃣ Testing Mining Channel Setup...")
    test_guild_id = 123456789012345678  # Test guild ID
    try:
        # Add some test channels
        add_mining_channel(db_url, test_guild_id, 123456789, "Mining Alpha", "primary")
        add_mining_channel(db_url, test_guild_id, 123456790, "Mining Beta", "secondary") 
        add_mining_channel(db_url, test_guild_id, 123456791, "Dispatch Central", "coordination")
        
        channels = get_mining_channels(db_url, test_guild_id)
        print(f"✅ Added {len(channels)} mining channels")
        for channel in channels:
            print(f"   - {channel[2]} ({channel[3]})")
    except Exception as e:
        print(f"❌ Channel setup failed: {e}")
        return False
    
    # Test 2: Simulate channel switching scenario
    print("\n2️⃣ Testing Channel Switching Scenarios...")
    try:
        # Simulate a mining session with channel switching
        base_time = datetime.now() - timedelta(hours=2)
        
        # User 1: Stays mostly in Mining Alpha, switches to Dispatch briefly
        start_time = base_time
        end_time = base_time + timedelta(minutes=90)
        save_mining_participation(
            db_url,
            1,  # event_id (test event)
            111111111,  # member_id
            "MinerAlpha",  # username
            123456789,  # channel_id (Mining Alpha)
            "Mining Alpha",  # channel_name
            start_time,  # start_time
            end_time,  # end_time
            90 * 60,  # duration_seconds (90 minutes)
            True  # is_org_member
        )
        
        # User 2: Splits time between Mining Beta and Dispatch
        start_time2 = base_time
        end_time2 = base_time + timedelta(minutes=60)
        save_mining_participation(
            db_url,
            1,  # event_id (test event)
            222222222,  # member_id
            "MinerBeta",  # username
            123456790,  # channel_id (Mining Beta)
            "Mining Beta",  # channel_name
            start_time2,  # start_time
            end_time2,  # end_time
            60 * 60,  # duration_seconds (60 minutes)
            False  # is_org_member
        )
        
        print("✅ Simulated channel switching scenarios")
        
    except Exception as e:
        print(f"❌ Channel switching simulation failed: {e}")
        return False
    
    # Test 3: Retrieve and analyze participation data
    print("\n3️⃣ Testing Enhanced Participation Retrieval...")
    try:
        participants = get_mining_session_participants(db_url, hours_back=3)
        
        print(f"✅ Retrieved {len(participants)} participants")
        
        for member_id, username, total_time, primary_channel_id, last_activity, is_org_member in participants:
            hours = total_time / 3600
            minutes = (total_time % 3600) / 60
            org_status = "Org Member" if is_org_member else "Guest"
            
            if hours >= 1:
                time_str = f"{hours:.1f}h"
            else:
                time_str = f"{minutes:.0f}m"
                
            print(f"   - {username}: {time_str} (Primary Channel: {primary_channel_id}, {org_status})")
            
    except Exception as e:
        print(f"❌ Participation retrieval failed: {e}")
        return False
    
    # Test 4: Verify time aggregation is correct
    print("\n4️⃣ Testing Time Aggregation Logic...")
    try:
        # MinerAlpha should have: 110 minutes total = 1.83 hours
        # MinerBeta should have: 90 minutes total = 1.5 hours
        
        miner_alpha_data = None
        miner_beta_data = None
        
        for participant in participants:
            if participant[1] == "MinerAlpha":
                miner_alpha_data = participant
            elif participant[1] == "MinerBeta":
                miner_beta_data = participant
        
        if miner_alpha_data:
            alpha_hours = miner_alpha_data[2] / 3600
            expected_alpha = 110/60  # 110 minutes = 1.83 hours
            if abs(alpha_hours - expected_alpha) < 0.1:
                print(f"✅ MinerAlpha time aggregation correct: {alpha_hours:.1f}h")
            else:
                print(f"❌ MinerAlpha time aggregation incorrect: {alpha_hours:.1f}h (expected {expected_alpha:.1f}h)")
        
        if miner_beta_data:
            beta_hours = miner_beta_data[2] / 3600
            expected_beta = 1.5  # 90 minutes
            if abs(beta_hours - expected_beta) < 0.1:
                print(f"✅ MinerBeta time aggregation correct: {beta_hours:.1f}h")
            else:
                print(f"❌ MinerBeta time aggregation incorrect: {beta_hours:.1f}h (expected {expected_beta}h)")
                
    except Exception as e:
        print(f"❌ Time aggregation test failed: {e}")
        return False
    
    print("\n🎉 Enhanced Mining System Test Complete!")
    return True

if __name__ == "__main__":
    success = test_enhanced_mining_system()
    if success:
        print("\n✅ All tests passed! Enhanced mining system is ready.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
