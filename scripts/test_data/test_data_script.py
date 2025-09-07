#!/usr/bin/env python3
"""
Test Data Generator for Red Legion Mining System
Creates realistic test data for Sunday mining sessions including:
- Mining events with proper lifecycle flags
- Participant data with voice tracking times
- Multiple channel participation
- Mix of org members and guests
"""

import asyncio
import random
import psycopg2
from datetime import datetime, timedelta
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.config import get_database_url

class MiningTestDataGenerator:
    def __init__(self, guild_id=None):
        self.db_url = get_database_url()
        self.test_data_ids = {
            'events': [],
            'participants': [],
            'channels': []
        }
        
        # Test Discord IDs (configurable or default)
        self.test_guild_id = guild_id if guild_id else 123456789012345678
        self.test_channels = {
            'Mining Alpha': 111111111111111111,
            'Mining Beta': 222222222222222222,
            'Mining Gamma': 333333333333333333,
            'Mining Delta': 444444444444444444
        }
        
        # Test participants (mix of org members and guests)
        self.test_participants = [
            # Org members
            {'id': 100001, 'username': 'CommanderSteel', 'is_org': True},
            {'id': 100002, 'username': 'MinerMax42', 'is_org': True},
            {'id': 100003, 'username': 'QuantumQueen', 'is_org': True},
            {'id': 100004, 'username': 'RockCrusher', 'is_org': True},
            {'id': 100005, 'username': 'AsteroidAce', 'is_org': True},
            {'id': 100006, 'username': 'OreMaster', 'is_org': True},
            {'id': 100007, 'username': 'DigDeepDan', 'is_org': True},
            {'id': 100008, 'username': 'CrystalHunter', 'is_org': True},
            
            # Guests
            {'id': 200001, 'username': 'GuestMiner1', 'is_org': False},
            {'id': 200002, 'username': 'NewbiePilot', 'is_org': False},
            {'id': 200003, 'username': 'TrialMember', 'is_org': False},
            {'id': 200004, 'username': 'FriendOfLegion', 'is_org': False},
        ]

    async def connect_db(self):
        """Connect to database."""
        try:
            self.conn = psycopg2.connect(self.db_url)
            self.cursor = self.conn.cursor()
            print("✅ Connected to database")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    def close_db(self):
        """Close database connection."""
        if hasattr(self, 'cursor'):
            self.cursor.close()
        if hasattr(self, 'conn'):
            self.conn.close()
        print("🔌 Database connection closed")

    async def create_test_mining_channels(self):
        """Create test mining channels in database."""
        try:
            print("\n📡 Creating test mining channels...")
            
            for channel_name, channel_id in self.test_channels.items():
                self.cursor.execute("""
                    INSERT INTO mining_channels (guild_id, channel_id, channel_name, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (guild_id, channel_id) DO NOTHING
                """, (self.test_guild_id, channel_id, channel_name, datetime.now()))
                
                self.test_data_ids['channels'].append((self.test_guild_id, channel_id))
            
            self.conn.commit()
            print(f"✅ Created {len(self.test_channels)} test mining channels")
            
        except Exception as e:
            print(f"❌ Error creating test channels: {e}")
            self.conn.rollback()

    async def create_test_mining_events(self, num_events=3):
        """Create test mining events with different states."""
        try:
            print(f"\n🎯 Creating {num_events} test mining events...")
            
            base_date = datetime.now().date()
            
            for i in range(num_events):
                event_date = base_date - timedelta(days=i * 7)  # Weekly Sunday events
                event_time = datetime.combine(event_date, datetime.min.time().replace(hour=14))  # 2 PM events
                
                # Vary event states for testing
                if i == 0:  # Most recent - open event
                    is_open = True
                    payroll_calculated = False
                    pdf_generated = False
                    status = "OPEN"
                elif i == 1:  # Previous week - completed
                    is_open = False
                    payroll_calculated = True
                    pdf_generated = True
                    status = "COMPLETED"
                else:  # Older - payroll done but no PDF
                    is_open = False
                    payroll_calculated = True
                    pdf_generated = False
                    status = "PAYROLL_DONE"
                
                self.cursor.execute("""
                    INSERT INTO events (guild_id, event_date, event_time, total_participants, 
                                      total_payout, is_open, payroll_calculated, pdf_generated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    self.test_guild_id, event_date, event_time,
                    random.randint(8, 12),  # Random participant count
                    random.randint(500000, 2000000) if payroll_calculated else None,  # Random payout
                    is_open, payroll_calculated, pdf_generated
                ))
                
                event_id = self.cursor.fetchone()[0]
                self.test_data_ids['events'].append(event_id)
                
                print(f"  📅 Event {event_id}: {event_date} ({status})")
                
                # Create participants for this event
                await self.create_test_participants_for_event(event_id, event_date)
            
            self.conn.commit()
            print(f"✅ Created {num_events} test mining events")
            
        except Exception as e:
            print(f"❌ Error creating test events: {e}")
            self.conn.rollback()

    async def create_test_participants_for_event(self, event_id, event_date):
        """Create realistic participant data for an event."""
        try:
            # Randomly select 8-12 participants for this event
            num_participants = random.randint(8, 12)
            selected_participants = random.sample(self.test_participants, num_participants)
            
            for participant in selected_participants:
                # Generate realistic mining session data
                start_time = datetime.combine(event_date, datetime.min.time().replace(
                    hour=14, minute=random.randint(0, 30)  # Join between 2:00-2:30 PM
                ))
                
                # Multiple channel sessions for channel-switching testing
                num_sessions = random.randint(1, 3)  # 1-3 different channels
                total_duration = 0
                primary_channel_id = None
                max_duration = 0
                
                for session_num in range(num_sessions):
                    # Pick a random channel
                    channel_name, channel_id = random.choice(list(self.test_channels.items()))
                    
                    # Generate session duration (30 minutes to 3 hours)
                    session_duration = random.randint(1800, 10800)  # 30 min to 3 hours in seconds
                    total_duration += session_duration
                    
                    # Track primary channel (longest session)
                    if session_duration > max_duration:
                        max_duration = session_duration
                        primary_channel_id = channel_id
                    
                    # Calculate end time
                    session_start = start_time + timedelta(seconds=sum([1800] * session_num))  # Stagger starts
                    session_end = session_start + timedelta(seconds=session_duration)
                    
                    # Insert participation record
                    self.cursor.execute("""
                        INSERT INTO mining_participation 
                        (event_id, member_id, username, channel_id, start_time, end_time, 
                         duration_seconds, is_org_member, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        event_id, participant['id'], participant['username'], channel_id,
                        session_start, session_end, session_duration, participant['is_org'],
                        datetime.now()
                    ))
                    
                    participation_id = self.cursor.fetchone()[0]
                    self.test_data_ids['participants'].append(participation_id)
                
                hours = total_duration / 3600
                org_status = "ORG" if participant['is_org'] else "GUEST"
                print(f"    👤 {participant['username']} ({org_status}): {hours:.1f}h across {num_sessions} channels")
            
        except Exception as e:
            print(f"❌ Error creating participants for event {event_id}: {e}")
            self.conn.rollback()

    async def show_test_data_summary(self):
        """Display summary of created test data."""
        try:
            print("\n📊 TEST DATA SUMMARY")
            print("=" * 50)
            
            # Events summary
            self.cursor.execute("""
                SELECT id, event_date, total_participants, total_payout, 
                       is_open, payroll_calculated, pdf_generated
                FROM events 
                WHERE guild_id = %s 
                ORDER BY event_date DESC
            """, (self.test_guild_id,))
            
            events = self.cursor.fetchall()
            print(f"\n📅 Mining Events ({len(events)}):")
            for event in events:
                event_id, date, participants, payout, is_open, payroll_calc, pdf_gen = event
                status = []
                if is_open:
                    status.append("OPEN")
                if payroll_calc:
                    status.append("PAYROLL")
                if pdf_gen:
                    status.append("PDF")
                status_str = " | ".join(status) if status else "CREATED"
                
                payout_str = f"{payout:,.0f} aUEC" if payout else "No payout"
                print(f"  Event {event_id}: {date} | {participants} participants | {payout_str} | {status_str}")
            
            # Participants summary
            self.cursor.execute("""
                SELECT username, COUNT(*) as sessions, SUM(duration_seconds) as total_time, is_org_member
                FROM mining_participation 
                WHERE event_id = ANY(%s)
                GROUP BY username, is_org_member
                ORDER BY total_time DESC
            """, (self.test_data_ids['events'],))
            
            participants = self.cursor.fetchall()
            print(f"\n👥 Participants ({len(participants)}):")
            for username, sessions, total_time, is_org in participants:
                hours = total_time / 3600
                org_badge = "🏢" if is_org else "👤"
                print(f"  {org_badge} {username}: {hours:.1f}h across {sessions} sessions")
            
            # Channels summary
            print(f"\n📡 Mining Channels ({len(self.test_channels)}):")
            for name, channel_id in self.test_channels.items():
                print(f"  {name}: {channel_id}")
            
        except Exception as e:
            print(f"❌ Error showing test data summary: {e}")

    async def cleanup_test_data(self):
        """Remove all test data from database."""
        try:
            print("\n🧹 CLEANING UP TEST DATA")
            print("=" * 50)
            
            # Delete participants
            if self.test_data_ids['participants']:
                self.cursor.execute("""
                    DELETE FROM mining_participation 
                    WHERE id = ANY(%s)
                """, (self.test_data_ids['participants'],))
                deleted_participants = self.cursor.rowcount
                print(f"🗑️  Deleted {deleted_participants} participation records")
            
            # Delete events
            if self.test_data_ids['events']:
                self.cursor.execute("""
                    DELETE FROM events 
                    WHERE id = ANY(%s)
                """, (self.test_data_ids['events'],))
                deleted_events = self.cursor.rowcount
                print(f"🗑️  Deleted {deleted_events} mining events")
            
            # Delete channels
            if self.test_data_ids['channels']:
                for guild_id, channel_id in self.test_data_ids['channels']:
                    self.cursor.execute("""
                        DELETE FROM mining_channels 
                        WHERE guild_id = %s AND channel_id = %s
                    """, (guild_id, channel_id))
                deleted_channels = self.cursor.rowcount
                print(f"🗑️  Deleted {len(self.test_data_ids['channels'])} mining channels")
            
            self.conn.commit()
            print("✅ All test data cleaned up successfully!")
            
            # Clear tracking arrays
            self.test_data_ids = {'events': [], 'participants': [], 'channels': []}
            
        except Exception as e:
            print(f"❌ Error cleaning up test data: {e}")
            self.conn.rollback()

async def main():
    """Main function with interactive menu."""
    generator = MiningTestDataGenerator()
    
    if not await generator.connect_db():
        return
    
    try:
        while True:
            print("\n" + "=" * 60)
            print("🔬 RED LEGION MINING SYSTEM - TEST DATA GENERATOR")
            print("=" * 60)
            print("1. 📊 Create Full Test Dataset")
            print("2. 📅 Create Test Events Only")
            print("3. 📡 Create Test Channels Only")
            print("4. 👁️  Show Current Test Data")
            print("5. 🧹 Clean Up All Test Data")
            print("6. 🚪 Exit")
            print("-" * 60)
            
            choice = input("Select option (1-6): ").strip()
            
            if choice == "1":
                print("\n🚀 Creating full test dataset...")
                await generator.create_test_mining_channels()
                await generator.create_test_mining_events(3)
                await generator.show_test_data_summary()
                
            elif choice == "2":
                await generator.create_test_mining_events(3)
                
            elif choice == "3":
                await generator.create_test_mining_channels()
                
            elif choice == "4":
                await generator.show_test_data_summary()
                
            elif choice == "5":
                confirm = input("⚠️  This will delete ALL test data. Continue? (y/N): ").strip().lower()
                if confirm == 'y':
                    await generator.cleanup_test_data()
                else:
                    print("❌ Cleanup cancelled")
                    
            elif choice == "6":
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please select 1-6.")
    
    finally:
        generator.close_db()

if __name__ == "__main__":
    asyncio.run(main())
