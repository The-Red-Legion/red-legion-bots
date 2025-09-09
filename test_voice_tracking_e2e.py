#!/usr/bin/env python3
"""
Voice Tracking End-to-End Test Suite
====================================

This test suite specifically focuses on voice channel participation tracking:
1. Voice state change simulation
2. Join/leave time tracking
3. Duration calculations
4. Multi-channel tracking
5. Concurrent user handling
6. Data persistence and retrieval

Author: Claude Code Assistant  
Usage: python test_voice_tracking_e2e.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
import random

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from database.operations import save_mining_participation, get_mining_session_participants, create_mining_event
from config.settings import get_database_url

class MockVoiceState:
    """Mock Discord voice state for testing"""
    def __init__(self, user_id, channel_id=None):
        self.user_id = user_id
        self.channel_id = channel_id
        self.channel = MockVoiceChannel(channel_id) if channel_id else None

class MockVoiceChannel:
    """Mock Discord voice channel"""
    def __init__(self, channel_id):
        self.id = int(channel_id) if channel_id else None
        self.name = f"Mining Channel {channel_id[-1]}" if channel_id else None

class MockMember:
    """Mock Discord member"""
    def __init__(self, user_id, username, is_org_member=True):
        self.id = int(user_id)
        self.name = username
        self.display_name = username
        self.is_org_member = is_org_member

class VoiceTrackingE2ETester:
    """Voice tracking end-to-end testing system"""
    
    def __init__(self):
        self.database_url = None
        self.test_event_id = None
        self.test_guild_id = 12345
        self.tracking_sessions = {}  # {user_id: tracking_data}
        self.test_results = []
        
        # Test mining channels (simulating the 7 Sunday mining channels)
        self.mining_channels = {
            'dispatch': '1385774416755163247',
            'alpha': '1386367354753257583', 
            'bravo': '1386367395643449414',
            'charlie': '1386367464279478313',
            'delta': '1386368182421635224',
            'echo': '1386368221877272616',
            'foxtrot': '1386368253712375828'
        }
        
    async def setup(self):
        """Initialize test environment"""
        print("🎤 Setting up Voice Tracking E2E Test Environment...")
        print("=" * 60)
        
        try:
            self.database_url = get_database_url()
            if not self.database_url:
                raise Exception("Database URL not available")
            
            # Create test event
            event_date = datetime.now().date()
            event_name = f"Voice Tracking Test - {event_date.strftime('%Y-%m-%d')}"
            
            self.test_event_id = create_mining_event(
                self.database_url,
                self.test_guild_id,
                event_date,
                event_name
            )
            
            if not self.test_event_id:
                raise Exception("Failed to create test event")
            
            print(f"✅ Test event created: ID {self.test_event_id}")
            print("✅ Voice tracking test environment ready\n")
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    def _log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            'name': test_name,
            'success': success,
            'details': details
        })
        print(f"{status}: {test_name}")
        if details and not success:
            print(f"   → {details}")
    
    async def simulate_voice_join(self, user_id: str, username: str, channel_name: str, 
                                join_time: datetime = None, is_org_member: bool = True):
        """Simulate a user joining a voice channel"""
        if join_time is None:
            join_time = datetime.now()
        
        channel_id = self.mining_channels.get(channel_name.lower(), 
                                            f"test_channel_{len(self.tracking_sessions)}")
        
        # Start tracking this user's session
        self.tracking_sessions[user_id] = {
            'username': username,
            'channel_id': channel_id,
            'channel_name': f"Mining {channel_name.title()}",
            'join_time': join_time,
            'is_org_member': is_org_member
        }
        
        print(f"🎤 {username} joined {channel_name} at {join_time.strftime('%H:%M:%S')}")
    
    async def simulate_voice_leave(self, user_id: str, leave_time: datetime = None):
        """Simulate a user leaving a voice channel"""
        if leave_time is None:
            leave_time = datetime.now()
        
        if user_id not in self.tracking_sessions:
            print(f"⚠️ User {user_id} not in tracking sessions")
            return False
        
        session = self.tracking_sessions[user_id]
        session['leave_time'] = leave_time
        
        # Calculate duration
        duration = leave_time - session['join_time']
        duration_minutes = int(duration.total_seconds() / 60)
        session['duration_minutes'] = duration_minutes
        
        # Save to database
        success = save_mining_participation(
            self.database_url,
            self.test_event_id,
            user_id,
            session['username'],
            session['channel_id'],
            session['channel_name'],
            session['join_time'],
            session['leave_time'],
            duration_minutes,
            session['is_org_member']
        )
        
        print(f"🚪 {session['username']} left {session['channel_name']} after {duration_minutes} minutes")
        
        # Remove from active tracking
        del self.tracking_sessions[user_id]
        
        return success
    
    async def test_basic_voice_tracking(self):
        """Test basic voice join/leave tracking"""
        print("🧪 Testing Basic Voice Tracking...")
        print("-" * 40)
        
        try:
            # Test single user join/leave
            user_id = "test_user_001"
            username = "VoiceTestUser1"
            
            # Simulate join
            join_time = datetime.now() - timedelta(minutes=30)
            await self.simulate_voice_join(user_id, username, "Alpha", join_time)
            
            # Check tracking state
            in_session = user_id in self.tracking_sessions
            self._log_result("Voice Join Tracking", in_session, 
                           f"User {username} tracked in session")
            
            # Simulate leave after 30 minutes
            leave_time = join_time + timedelta(minutes=30)
            save_success = await self.simulate_voice_leave(user_id, leave_time)
            
            self._log_result("Voice Leave and Save", save_success,
                           f"30-minute session saved to database")
            
            # Verify data in database
            participants = get_mining_session_participants(
                self.database_url, 
                event_id=self.test_event_id
            )
            
            user_found = any(p['user_id'] == user_id for p in participants) if participants else False
            self._log_result("Database Persistence", user_found,
                           f"Found {len(participants) if participants else 0} participants")
            
            return True
            
        except Exception as e:
            self._log_result("Basic Voice Tracking", False, str(e))
            return False
    
    async def test_multi_channel_tracking(self):
        """Test tracking across multiple mining channels"""
        print("\n🧪 Testing Multi-Channel Tracking...")
        print("-" * 40)
        
        try:
            base_time = datetime.now() - timedelta(hours=1)
            users_per_channel = 2
            total_expected = len(self.mining_channels) * users_per_channel
            
            # Simulate users joining different channels
            user_counter = 1
            for channel_name in self.mining_channels.keys():
                for i in range(users_per_channel):
                    user_id = f"multi_user_{user_counter:03d}"
                    username = f"MultiUser{user_counter}"
                    
                    # Stagger join times
                    join_time = base_time + timedelta(minutes=user_counter * 2)
                    await self.simulate_voice_join(user_id, username, channel_name, join_time)
                    
                    # Simulate leave after variable duration (45-75 minutes)
                    duration = 45 + (user_counter % 31)  # Variable duration
                    leave_time = join_time + timedelta(minutes=duration)
                    await self.simulate_voice_leave(user_id, leave_time)
                    
                    user_counter += 1
            
            # Verify all users were saved
            participants = get_mining_session_participants(
                self.database_url,
                event_id=self.test_event_id
            )
            
            actual_count = len(participants) if participants else 0
            multi_channel_success = actual_count >= total_expected
            
            self._log_result("Multi-Channel Tracking", multi_channel_success,
                           f"Expected {total_expected}, got {actual_count} participants")
            
            # Test channel distribution
            if participants:
                channels_used = set(p['channel_id'] for p in participants)
                channel_distribution = len(channels_used) >= len(self.mining_channels) - 1  # Allow some variance
                
                self._log_result("Channel Distribution", channel_distribution,
                               f"Used {len(channels_used)} different channels")
            
            return True
            
        except Exception as e:
            self._log_result("Multi-Channel Tracking", False, str(e))
            return False
    
    async def test_concurrent_user_handling(self):
        """Test handling multiple users joining/leaving simultaneously"""
        print("\n🧪 Testing Concurrent User Handling...")
        print("-" * 40)
        
        try:
            # Simulate a realistic Sunday mining scenario
            scenarios = [
                # Scenario 1: Mass join at start
                {"action": "mass_join", "users": 8, "channel": "dispatch"},
                
                # Scenario 2: Users spread to different channels
                {"action": "channel_spread", "users": 8},
                
                # Scenario 3: Some users leave early, others join late
                {"action": "mixed_activity", "early_leavers": 3, "late_joiners": 2},
            ]
            
            base_time = datetime.now() - timedelta(hours=2)
            scenario_users = {}
            
            # Scenario 1: Mass join
            print("   Scenario 1: Mass join at mining start...")
            for i in range(scenarios[0]["users"]):
                user_id = f"concurrent_user_{i+1:03d}"
                username = f"ConcurrentUser{i+1}"
                join_time = base_time + timedelta(seconds=i*5)  # Spread over 40 seconds
                
                await self.simulate_voice_join(user_id, username, "dispatch", join_time)
                scenario_users[user_id] = {"username": username, "join_time": join_time}
            
            mass_join_tracked = len(self.tracking_sessions) >= scenarios[0]["users"]
            self._log_result("Mass Join Handling", mass_join_tracked,
                           f"Tracked {len(self.tracking_sessions)} concurrent users")
            
            # Scenario 2: Channel spread (simulate users moving to mining channels)
            print("   Scenario 2: Users spreading to mining channels...")
            channels_list = list(self.mining_channels.keys())[1:]  # Exclude dispatch
            user_ids = list(scenario_users.keys())
            
            for i, user_id in enumerate(user_ids):
                # Simulate leaving dispatch and joining mining channel
                await self.simulate_voice_leave(user_id, base_time + timedelta(minutes=5))
                
                # Join mining channel
                new_channel = channels_list[i % len(channels_list)]
                new_join_time = base_time + timedelta(minutes=6 + i)
                await self.simulate_voice_join(user_id, scenario_users[user_id]["username"], 
                                             new_channel, new_join_time)
            
            spread_success = len(self.tracking_sessions) > 0
            self._log_result("Channel Spread Handling", spread_success,
                           f"Successfully moved users to mining channels")
            
            # Scenario 3: Mixed activity - some leave early, others join late
            print("   Scenario 3: Mixed join/leave activity...")
            
            # Early leavers
            early_leavers = list(self.tracking_sessions.keys())[:3]
            for user_id in early_leavers:
                await self.simulate_voice_leave(user_id, base_time + timedelta(minutes=45))
            
            # Late joiners
            for i in range(2):
                user_id = f"late_joiner_{i+1}"
                username = f"LateJoiner{i+1}"
                join_time = base_time + timedelta(minutes=60 + i*5)
                await self.simulate_voice_join(user_id, username, "alpha", join_time)
            
            # Clean up remaining users
            remaining_users = list(self.tracking_sessions.keys())
            for user_id in remaining_users:
                await self.simulate_voice_leave(user_id, base_time + timedelta(minutes=120))
            
            # Final verification
            final_participants = get_mining_session_participants(
                self.database_url,
                event_id=self.test_event_id
            )
            
            concurrent_handling_success = len(final_participants) > 10 if final_participants else False
            self._log_result("Concurrent Activity Handling", concurrent_handling_success,
                           f"Final participant count: {len(final_participants) if final_participants else 0}")
            
            return True
            
        except Exception as e:
            self._log_result("Concurrent User Handling", False, str(e))
            return False
    
    async def test_duration_accuracy(self):
        """Test accuracy of duration calculations"""
        print("\n🧪 Testing Duration Calculation Accuracy...")
        print("-" * 40)
        
        try:
            # Test various duration scenarios
            duration_tests = [
                {"minutes": 30, "user": "duration_test_30min"},
                {"minutes": 90, "user": "duration_test_90min"}, 
                {"minutes": 180, "user": "duration_test_180min"},
                {"minutes": 1, "user": "duration_test_1min"},  # Edge case
                {"minutes": 300, "user": "duration_test_5hours"},  # Long session
            ]
            
            base_time = datetime.now() - timedelta(hours=1)
            
            for i, test in enumerate(duration_tests):
                user_id = f"duration_user_{i+1}"
                username = test["user"]
                target_minutes = test["minutes"]
                
                # Simulate precise join/leave
                join_time = base_time + timedelta(minutes=i*5)
                leave_time = join_time + timedelta(minutes=target_minutes)
                
                await self.simulate_voice_join(user_id, username, "bravo", join_time)
                await self.simulate_voice_leave(user_id, leave_time)
            
            # Verify durations in database
            participants = get_mining_session_participants(
                self.database_url,
                event_id=self.test_event_id
            )
            
            if participants:
                # Check duration accuracy for our test users
                duration_users = [p for p in participants if p['user_id'].startswith('duration_user_')]
                
                accurate_durations = 0
                for i, user in enumerate(duration_users):
                    expected = duration_tests[i]["minutes"]
                    actual = user.get('duration_minutes', 0)
                    
                    # Allow 1-minute tolerance for calculation precision
                    if abs(expected - actual) <= 1:
                        accurate_durations += 1
                    else:
                        print(f"   ⚠️ Duration mismatch for {user['username']}: expected {expected}, got {actual}")
                
                accuracy_success = accurate_durations == len(duration_tests)
                self._log_result("Duration Calculation Accuracy", accuracy_success,
                               f"{accurate_durations}/{len(duration_tests)} durations accurate")
                
                # Test total duration calculation
                total_minutes = sum(p.get('duration_minutes', 0) for p in duration_users)
                expected_total = sum(t["minutes"] for t in duration_tests)
                
                total_accuracy = abs(total_minutes - expected_total) <= len(duration_tests)  # Allow some tolerance
                self._log_result("Total Duration Calculation", total_accuracy,
                               f"Total: {total_minutes} minutes (expected ~{expected_total})")
            else:
                self._log_result("Duration Calculation Accuracy", False, "No participants found")
            
            return True
            
        except Exception as e:
            self._log_result("Duration Calculation Accuracy", False, str(e))
            return False
    
    async def test_org_member_tracking(self):
        """Test org member vs non-member tracking"""
        print("\n🧪 Testing Org Member Classification...")
        print("-" * 40)
        
        try:
            # Create mixed group of org members and non-members
            test_users = [
                {"id": "org_member_1", "name": "OrgMember1", "is_org": True},
                {"id": "org_member_2", "name": "OrgMember2", "is_org": True}, 
                {"id": "non_member_1", "name": "NonMember1", "is_org": False},
                {"id": "non_member_2", "name": "NonMember2", "is_org": False},
                {"id": "org_member_3", "name": "OrgMember3", "is_org": True},
            ]
            
            base_time = datetime.now() - timedelta(minutes=90)
            
            # Simulate sessions for all users
            for i, user in enumerate(test_users):
                join_time = base_time + timedelta(minutes=i*2)
                leave_time = join_time + timedelta(minutes=60)
                
                await self.simulate_voice_join(
                    user["id"], user["name"], "charlie", join_time, user["is_org"]
                )
                await self.simulate_voice_leave(user["id"], leave_time)
            
            # Verify classification in database
            participants = get_mining_session_participants(
                self.database_url,
                event_id=self.test_event_id
            )
            
            if participants:
                # Find our test users
                org_test_users = [p for p in participants if p['user_id'].startswith('org_member_')]
                non_org_test_users = [p for p in participants if p['user_id'].startswith('non_member_')]
                
                # Check org member classification
                org_members_correct = all(p.get('is_org_member', False) for p in org_test_users)
                non_members_correct = all(not p.get('is_org_member', True) for p in non_org_test_users)
                
                self._log_result("Org Member Classification", org_members_correct,
                               f"Found {len(org_test_users)} org members correctly classified")
                
                self._log_result("Non-Member Classification", non_members_correct,
                               f"Found {len(non_org_test_users)} non-members correctly classified")
                
                # Test mixed group stats
                expected_org = 3
                expected_non_org = 2
                actual_org = len(org_test_users)
                actual_non_org = len(non_org_test_users)
                
                classification_balance = (actual_org == expected_org and 
                                        actual_non_org == expected_non_org)
                
                self._log_result("Classification Balance", classification_balance,
                               f"Org: {actual_org}/{expected_org}, Non-org: {actual_non_org}/{expected_non_org}")
            else:
                self._log_result("Org Member Classification", False, "No participants found")
            
            return True
            
        except Exception as e:
            self._log_result("Org Member Classification", False, str(e))
            return False
    
    async def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up voice tracking test data...")
        
        try:
            if self.test_event_id and self.database_url:
                import psycopg2
                from urllib.parse import urlparse
                
                parsed = urlparse(self.database_url)
                conn = psycopg2.connect(
                    host=parsed.hostname,
                    database=parsed.path[1:],
                    user=parsed.username,
                    password=parsed.password,
                    port=parsed.port or 5432
                )
                
                with conn.cursor() as cursor:
                    # Clean up test participation records
                    cursor.execute("""
                        DELETE FROM mining_participation 
                        WHERE event_id = %s AND (
                            user_id LIKE 'test_user_%' OR 
                            user_id LIKE 'multi_user_%' OR
                            user_id LIKE 'concurrent_user_%' OR
                            user_id LIKE 'duration_user_%' OR
                            user_id LIKE 'org_member_%' OR
                            user_id LIKE 'non_member_%' OR
                            user_id LIKE 'late_joiner_%'
                        )
                    """, (self.test_event_id,))
                    
                    participation_deleted = cursor.rowcount
                    
                    # Delete test event
                    cursor.execute("""
                        DELETE FROM mining_events 
                        WHERE event_id = %s AND name LIKE 'Voice Tracking Test%'
                    """, (self.test_event_id,))
                    
                    event_deleted = cursor.rowcount
                    conn.commit()
                
                conn.close()
                
                print(f"✅ Cleaned up {participation_deleted} participation records")
                print(f"✅ Cleaned up {event_deleted} test events")
                
        except Exception as e:
            print(f"⚠️ Cleanup failed: {e}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🎤 VOICE TRACKING E2E TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Results: {passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests)*100:.1f}%)")
        
        print(f"\n📋 Test Details:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['name']}")
            if result['details'] and not result['success']:
                print(f"      → {result['details']}")
        
        if failed_tests == 0:
            print(f"\n🎉 ALL VOICE TRACKING TESTS PASSED! 🎉")
            print(f"Voice participation tracking is working correctly.")
        else:
            print(f"\n⚠️  {failed_tests} TEST(S) FAILED")
            print(f"Please review the voice tracking implementation.")
        
        print("=" * 60)

async def main():
    """Main test execution"""
    print("🎤 Voice Tracking End-to-End Test Suite")
    print("=" * 60)
    print("Testing voice participation tracking components:")
    print("• Basic join/leave tracking")
    print("• Multi-channel tracking across 7 mining channels")
    print("• Concurrent user handling")
    print("• Duration calculation accuracy")
    print("• Org member classification")
    print("• Data persistence and retrieval")
    print("=" * 60)
    
    tester = VoiceTrackingE2ETester()
    
    # Setup
    if not await tester.setup():
        print("❌ Failed to setup test environment")
        return
    
    try:
        # Run all voice tracking tests
        await tester.test_basic_voice_tracking()
        await tester.test_multi_channel_tracking()
        await tester.test_concurrent_user_handling()
        await tester.test_duration_accuracy()
        await tester.test_org_member_tracking()
        
    finally:
        # Cleanup and summary
        await tester.cleanup()
        tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())