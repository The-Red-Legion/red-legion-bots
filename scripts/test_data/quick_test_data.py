#!/usr/bin/env python3
"""
Quick Test Data Script for Red Legion Mining System
Standalone script that can populate and clean test data for mining system testing.
Run this before testing the mining bot to have realistic data to work with.
"""

import random
import psycopg2
from datetime import datetime, timedelta
import os

class QuickTestData:
    def __init__(self, guild_id=None):
        # Get database URL from environment or file
        self.db_url = self._get_database_url()
        self.conn = None
        self.cursor = None
        
        # Test Discord server/channel IDs (configurable or default)
        self.test_guild_id = guild_id if guild_id else 123456789012345678
        self.test_channels = {
            'Mining Alpha': 111111111111111111,
            'Mining Beta': 222222222222222222,  
            'Mining Gamma': 333333333333333333,
            'Mining Delta': 444444444444444444
        }
        
        # Test participants with realistic Discord usernames
        self.participants = [
            # Red Legion Members
            {'id': 100001, 'username': 'CommanderSteel', 'org': True},
            {'id': 100002, 'username': 'MinerMax42', 'org': True},
            {'id': 100003, 'username': 'QuantumQueen', 'org': True},
            {'id': 100004, 'username': 'RockCrusher_RL', 'org': True},
            {'id': 100005, 'username': 'AsteroidAce', 'org': True},
            {'id': 100006, 'username': 'OreMaster_RedLegion', 'org': True},
            {'id': 100007, 'username': 'DigDeepDan', 'org': True},
            {'id': 100008, 'username': 'CrystalHunter88', 'org': True},
            
            # Guest Miners
            {'id': 200001, 'username': 'GuestMiner_1', 'org': False},
            {'id': 200002, 'username': 'NewbiePilot', 'org': False},
            {'id': 200003, 'username': 'TrialMember_99', 'org': False},
            {'id': 200004, 'username': 'FriendOfLegion', 'org': False},
        ]
        
        # Track created data for cleanup
        self.created_data = {
            'events': [],
            'participants': [],
            'channels': []
        }

    def _get_database_url(self):
        """Get database URL from various sources."""
        # Try environment variable first
        if 'DATABASE_URL' in os.environ:
            return os.environ['DATABASE_URL']
        
        # Try reading from db_url.txt file
        db_file_path = os.path.join(os.path.dirname(__file__), 'db_url.txt')
        if os.path.exists(db_file_path):
            with open(db_file_path, 'r') as f:
                return f.read().strip()
        
        return None

    def connect(self):
        """Connect to database."""
        if not self.db_url:
            print("❌ No database URL found. Set DATABASE_URL env var or create db_url.txt")
            return False
        
        try:
            self.conn = psycopg2.connect(self.db_url)
            self.cursor = self.conn.cursor()
            print("✅ Connected to database")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    def close(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def create_test_channels(self):
        """Create test mining channels."""
        print("📡 Creating test mining channels...")
        try:
            for name, channel_id in self.test_channels.items():
                self.cursor.execute("""
                    INSERT INTO mining_channels (guild_id, channel_id, channel_name, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (guild_id, channel_id) DO NOTHING
                """, (self.test_guild_id, channel_id, name, datetime.now()))
                
                self.created_data['channels'].append((self.test_guild_id, channel_id))
            
            self.conn.commit()
            print(f"✅ Created {len(self.test_channels)} test channels")
        except Exception as e:
            print(f"❌ Error creating channels: {e}")
            self.conn.rollback()

    def create_test_events(self):
        """Create test mining events with different states."""
        print("🎯 Creating test mining events...")
        try:
            today = datetime.now().date()
            
            # Event 1: Open event (current Sunday session)
            event1_date = today
            event1_time = datetime.combine(event1_date, datetime.min.time().replace(hour=14))
            
            self.cursor.execute("""
                INSERT INTO events (guild_id, event_date, event_time, total_participants, 
                                  total_payout, is_open, payroll_calculated, pdf_generated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (self.test_guild_id, event1_date, event1_time, 10, None, True, False, False))
            
            event1_id = self.cursor.fetchone()[0]
            self.created_data['events'].append(event1_id)
            print(f"  📅 Event {event1_id}: {event1_date} (OPEN - Active Session)")
            
            # Event 2: Completed event (last week)
            event2_date = today - timedelta(days=7)
            event2_time = datetime.combine(event2_date, datetime.min.time().replace(hour=14))
            
            self.cursor.execute("""
                INSERT INTO events (guild_id, event_date, event_time, total_participants, 
                                  total_payout, is_open, payroll_calculated, pdf_generated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (self.test_guild_id, event2_date, event2_time, 8, 1500000, False, True, True))
            
            event2_id = self.cursor.fetchone()[0]
            self.created_data['events'].append(event2_id)
            print(f"  📅 Event {event2_id}: {event2_date} (COMPLETED - 1.5M aUEC)")
            
            # Event 3: Payroll done, no PDF (2 weeks ago)
            event3_date = today - timedelta(days=14)
            event3_time = datetime.combine(event3_date, datetime.min.time().replace(hour=14))
            
            self.cursor.execute("""
                INSERT INTO events (guild_id, event_date, event_time, total_participants, 
                                  total_payout, is_open, payroll_calculated, pdf_generated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (self.test_guild_id, event3_date, event3_time, 12, 2100000, False, True, False))
            
            event3_id = self.cursor.fetchone()[0]
            self.created_data['events'].append(event3_id)
            print(f"  📅 Event {event3_id}: {event3_date} (PAYROLL DONE - 2.1M aUEC)")
            
            # Create participants for all events
            self.create_participants_for_event(event1_id, event1_date, "open")
            self.create_participants_for_event(event2_id, event2_date, "completed")
            self.create_participants_for_event(event3_id, event3_date, "payroll_done")
            
            self.conn.commit()
            print("✅ Created 3 test events with different states")
            
        except Exception as e:
            print(f"❌ Error creating events: {e}")
            self.conn.rollback()

    def create_participants_for_event(self, event_id, event_date, event_type):
        """Create realistic participant data for an event."""
        try:
            # Different participation patterns based on event type
            if event_type == "open":
                # Current session - some people still mining
                num_participants = random.randint(6, 10)
            else:
                # Completed sessions
                num_participants = random.randint(8, 12)
            
            selected = random.sample(self.participants, num_participants)
            
            for participant in selected:
                # Generate realistic mining times
                num_channel_sessions = random.randint(1, 3)  # Channel switching
                
                for session in range(num_channel_sessions):
                    channel_name, channel_id = random.choice(list(self.test_channels.items()))
                    
                    # Different time patterns
                    if event_type == "open":
                        # Current session - shorter times, some still active
                        duration = random.randint(1800, 7200)  # 30min to 2h
                    else:
                        # Completed sessions - longer times
                        duration = random.randint(3600, 12600)  # 1h to 3.5h
                    
                    # Calculate session times
                    start_offset = random.randint(0, 1800) + (session * 1800)  # Stagger starts
                    start_time = datetime.combine(event_date, datetime.min.time().replace(hour=14)) + timedelta(seconds=start_offset)
                    end_time = start_time + timedelta(seconds=duration)
                    
                    self.cursor.execute("""
                        INSERT INTO mining_participation 
                        (event_id, member_id, username, channel_id, start_time, end_time, 
                         duration_seconds, is_org_member, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        event_id, participant['id'], participant['username'], channel_id,
                        start_time, end_time, duration, participant['org'], datetime.now()
                    ))
                    
                    part_id = self.cursor.fetchone()[0]
                    self.created_data['participants'].append(part_id)
                    
                    hours = duration / 3600
                    org_badge = "🏢" if participant['org'] else "👤"
                    channel_short = channel_name.replace('Mining ', '')
                    print(f"    {org_badge} {participant['username']}: {hours:.1f}h in {channel_short}")
            
        except Exception as e:
            print(f"❌ Error creating participants for event {event_id}: {e}")

    def show_summary(self):
        """Show summary of test data."""
        print("\n📊 TEST DATA SUMMARY")
        print("=" * 50)
        
        try:
            # Events
            self.cursor.execute("""
                SELECT id, event_date, total_participants, total_payout, 
                       is_open, payroll_calculated, pdf_generated
                FROM events WHERE guild_id = %s ORDER BY event_date DESC
            """, (self.test_guild_id,))
            
            events = self.cursor.fetchall()
            print(f"\n📅 Events ({len(events)}):")
            for event_id, date, participants, payout, is_open, payroll, pdf in events:
                status = []
                if is_open: status.append("🟢 OPEN")
                if payroll: status.append("💰 PAYROLL")
                if pdf: status.append("📄 PDF")
                status_str = " ".join(status) if status else "⚪ CREATED"
                
                payout_str = f"{payout:,.0f} aUEC" if payout else "No payout"
                print(f"  Event {event_id}: {date} | {participants} miners | {payout_str} | {status_str}")
            
            # Top participants
            self.cursor.execute("""
                SELECT username, SUM(duration_seconds) as total_time, is_org_member,
                       COUNT(*) as sessions
                FROM mining_participation 
                WHERE event_id = ANY(%s)
                GROUP BY username, is_org_member
                ORDER BY total_time DESC LIMIT 8
            """, (self.created_data['events'],))
            
            participants = self.cursor.fetchall()
            print(f"\n👥 Top Participants:")
            for username, total_time, is_org, sessions in participants:
                hours = total_time / 3600
                org_badge = "🏢" if is_org else "👤"
                print(f"  {org_badge} {username}: {hours:.1f}h ({sessions} sessions)")
                
        except Exception as e:
            print(f"❌ Error showing summary: {e}")

    def cleanup(self):
        """Clean up all test data."""
        print("\n🧹 CLEANING UP TEST DATA")
        print("=" * 50)
        
        try:
            # Delete participants
            if self.created_data['participants']:
                self.cursor.execute("DELETE FROM mining_participation WHERE id = ANY(%s)", 
                                  (self.created_data['participants'],))
                print(f"🗑️  Deleted {self.cursor.rowcount} participation records")
            
            # Delete events
            if self.created_data['events']:
                self.cursor.execute("DELETE FROM events WHERE id = ANY(%s)", 
                                  (self.created_data['events'],))
                print(f"🗑️  Deleted {self.cursor.rowcount} events")
            
            # Delete channels
            for guild_id, channel_id in self.created_data['channels']:
                self.cursor.execute("DELETE FROM mining_channels WHERE guild_id = %s AND channel_id = %s", 
                                  (guild_id, channel_id))
            print(f"🗑️  Deleted {len(self.created_data['channels'])} channels")
            
            self.conn.commit()
            self.created_data = {'events': [], 'participants': [], 'channels': []}
            print("✅ All test data cleaned up!")
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            self.conn.rollback()


def main():
    """Interactive menu for test data management."""
    test_data = QuickTestData()
    
    if not test_data.connect():
        return
    
    try:
        while True:
            print("\n" + "=" * 50)
            print("🔬 MINING SYSTEM TEST DATA MANAGER")
            print("=" * 50)
            print("1. 🚀 Create Full Test Dataset")
            print("2. 📊 Show Current Data")
            print("3. 🧹 Clean Up Test Data")
            print("4. 🚪 Exit")
            print("-" * 50)
            
            choice = input("Select option (1-4): ").strip()
            
            if choice == "1":
                print("\n🚀 Creating complete test dataset...")
                test_data.create_test_channels()
                test_data.create_test_events()
                test_data.show_summary()
                print("\n✅ Test data ready! You can now test the mining bot commands.")
                
            elif choice == "2":
                test_data.show_summary()
                
            elif choice == "3":
                confirm = input("\n⚠️  Delete ALL test data? (y/N): ").strip().lower()
                if confirm == 'y':
                    test_data.cleanup()
                else:
                    print("❌ Cleanup cancelled")
                    
            elif choice == "4":
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please select 1-4.")
    
    finally:
        test_data.close()


if __name__ == "__main__":
    main()
