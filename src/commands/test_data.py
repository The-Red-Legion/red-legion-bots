"""
Test data generation command for the unified mining system.
Creates dummy events and participation data for testing the payroll module.
"""

import discord
from discord import app_commands, ui
from discord.ext import commands
from datetime import datetime, timedelta
import random
import string
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestDataCreationModal(ui.Modal):
    """Modal for creating test data with custom parameters."""
    
    def __init__(self):
        super().__init__(title='Create Test Mining Event')
        
        self.participants = ui.TextInput(
            label='Number of Participants',
            placeholder='10',
            default='10',
            required=True,
            max_length=2
        )
        
        self.hours_ago = ui.TextInput(
            label='Hours Ago (when event started)',
            placeholder='4',
            default='4',
            required=True,
            max_length=2
        )
        
        self.duration = ui.TextInput(
            label='Event Duration (hours)',
            placeholder='3.5',
            default='3.5',
            required=True,
            max_length=4
        )
        
        self.location = ui.TextInput(
            label='Mining Location (optional)',
            placeholder='Random location will be chosen',
            required=False,
            max_length=50
        )
        
        self.event_name = ui.TextInput(
            label='Event Name (optional)',
            placeholder='Test Mining Event at [Location]',
            required=False,
            max_length=100
        )
        
        self.add_item(self.participants)
        self.add_item(self.hours_ago)
        self.add_item(self.duration)
        self.add_item(self.location)
        self.add_item(self.event_name)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            # Parse and validate inputs
            participants = int(self.participants.value.strip())
            hours_ago = int(self.hours_ago.value.strip())
            duration = float(self.duration.value.strip())
            location = self.location.value.strip() if self.location.value.strip() else None
            event_name = self.event_name.value.strip() if self.event_name.value.strip() else None
            
            # Validate parameters
            if not (1 <= participants <= 50):
                await interaction.followup.send("❌ Participants must be between 1 and 50", ephemeral=True)
                return
            
            if not (0 <= hours_ago <= 48):
                await interaction.followup.send("❌ Hours ago must be between 0 and 48", ephemeral=True)
                return
            
            if not (0.5 <= duration <= 12):
                await interaction.followup.send("❌ Duration must be between 0.5 and 12 hours", ephemeral=True)
                return
            
            # Show creating progress message
            progress_message = await interaction.followup.send(
                embed=discord.Embed(
                    title="⏳ Creating Test Event",
                    description=f"Creating test mining event with {participants} participants...",
                    color=discord.Color.blue()
                )
            )
            
            # Create test data
            result = await self._create_test_event(interaction, participants, hours_ago, duration, location, event_name)
            
            if result['success']:
                embed = discord.Embed(
                    title="✅ Test Mining Event Created",
                    description=f"Successfully created test event `{result['event_id']}` with dummy participation data",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(name="Event ID", value=f"`{result['event_id']}`", inline=True)
                embed.add_field(name="Location", value=result['location'], inline=True)
                embed.add_field(name="Status", value="Closed (Ready for payroll)", inline=True)
                
                embed.add_field(name="Event Start", value=f"<t:{int(result['event_start'].timestamp())}:R>", inline=True)
                embed.add_field(name="Event Duration", value=f"{duration} hours", inline=True)
                embed.add_field(name="Participants", value=f"{participants}", inline=True)
                
                embed.add_field(name="Participation Records", value=f"{result['participation_records']}", inline=True)
                embed.add_field(name="Total Participation Time", value=f"{result['total_participation_time']:,} minutes", inline=True)
                embed.add_field(name="Avg Time per Participant", value=f"{result['avg_participation']:.1f} minutes", inline=True)
                
                embed.add_field(
                    name="🧪 Testing Commands",
                    value=f"• Use `/payroll calculate` to calculate payroll for this event\n"
                          f"• Use `/mining status` to see event details\n"
                          f"• Use `/test-data delete` when done testing",
                    inline=False
                )
                
                embed.set_footer(text="⚠️ Remember to clean up test data when finished!")
                
                await progress_message.edit(embed=embed)
            else:
                await progress_message.edit(
                    embed=discord.Embed(
                        title="❌ Error Creating Test Data",
                        description=result['error'],
                        color=discord.Color.red()
                    )
                )
        
        except ValueError as e:
            await interaction.followup.send(
                f"❌ Invalid input: Please enter valid numbers for participants, hours, and duration.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error creating test data: {str(e)}",
                ephemeral=True
            )
    
    async def _create_test_event(self, interaction, participants, hours_ago, duration, location, event_name):
        """Create test event and participation data."""
        try:
            # Import required modules
            from config.settings import get_database_url
            from database.connection import resolve_database_url
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            db_url = get_database_url()
            if not db_url:
                return {'success': False, 'error': 'Database connection not available'}
            
            # Generate event ID with SM- prefix for test data (using database constraint format)
            chars = '0123456789abcdefghijklmnopqrstuvwxyz'
            random_part = ''.join(random.choices(chars, k=6))
            event_id = f"sm-{random_part}"
            
            # Calculate event times
            event_start = datetime.now() - timedelta(hours=hours_ago)
            event_end = event_start + timedelta(hours=duration)
            
            location = location or random.choice([
                "Daymar", "Yela", "Aberdeen", "Magda", "Arial", "Lyria", 
                "Wala", "Cellin", "Hurston", "ArcCorp"
            ])
            
            event_name = event_name or f'Test Mining Event at {location}'
            
            # Connect to database
            resolved_url = resolve_database_url(db_url)
            conn = psycopg2.connect(resolved_url, cursor_factory=RealDictCursor)
            
            try:
                with conn.cursor() as cursor:
                    # Calculate event duration in minutes
                    event_duration_minutes = int((event_end - event_start).total_seconds() / 60)
                    
                    # Create test event in unified events table
                    cursor.execute("""
                        INSERT INTO events (
                            event_id, guild_id, event_type, event_name, organizer_id, organizer_name,
                            started_at, ended_at, status, location_notes, created_at,
                            total_duration_minutes, total_participants
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (event_id) DO NOTHING
                    """, (
                        event_id,
                        str(interaction.guild.id),
                        'mining',
                        event_name,
                        str(interaction.user.id),
                        interaction.user.display_name,
                        event_start,
                        event_end,
                        'closed',  # Mark as closed so payroll can be calculated
                        location,
                        datetime.now(),
                        event_duration_minutes,
                        participants  # Number of participants from form
                    ))
                    
                    # Create test participants and participation records
                    test_users_created = 0
                    participation_records = 0
                    total_participation_time = 0
                    
                    for i in range(participants):
                        # Generate test user ID (numeric for BIGINT field)
                        # Use a safe range starting from 9000000000000000000 to avoid conflicts
                        base_test_id = 9000000000000000000
                        # Extract suffix from event_id (e.g., "sm-a7k2m9" -> "a7k2m9") and convert to number
                        try:
                            event_suffix = event_id.split('-')[1] if '-' in event_id else event_id
                            # Convert alphanumeric suffix to number using hash for consistency
                            event_number = abs(hash(event_suffix)) % 100000  # Keep within reasonable range
                        except (IndexError, ValueError):
                            event_number = random.randint(10000, 99999)  # Fallback
                        user_id = base_test_id + (event_number * 1000) + i + 1
                        username = f"TestMiner{i+1:03d}"
                        is_org_member = random.choice([True, False])
                        
                        # Insert test user
                        cursor.execute("""
                            INSERT INTO users (user_id, username, display_name, first_seen, last_seen)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (user_id) DO NOTHING
                        """, (
                            user_id,
                            username,
                            username,
                            event_start,
                            event_end
                        ))
                        test_users_created += 1
                        
                        # Generate 1-4 participation sessions per user
                        num_sessions = random.randint(1, 4)
                        user_total_time = 0
                        
                        for session in range(num_sessions):
                            # Calculate available event duration
                            event_duration_minutes = int((event_end - event_start).total_seconds() / 60)
                            
                            # Random participation duration (15 minutes to min of 180 or event duration)
                            max_session_duration = min(180, event_duration_minutes - 5)  # Leave 5 min buffer
                            duration_minutes = random.randint(15, max(15, max_session_duration))
                            
                            # Calculate session times within event window  
                            max_start_offset = max(0, event_duration_minutes - duration_minutes)
                            min_start_offset = min(session * 30, max_start_offset)  # Don't exceed max
                            
                            if max_start_offset > min_start_offset:
                                start_offset = random.randint(min_start_offset, max_start_offset)
                            else:
                                start_offset = min_start_offset
                            
                            join_time = event_start + timedelta(minutes=start_offset)
                            leave_time = join_time + timedelta(minutes=duration_minutes)
                            
                            # Ensure we don't go past event end
                            if leave_time > event_end:
                                leave_time = event_end
                                duration_minutes = int((leave_time - join_time).total_seconds() / 60)
                            
                            if duration_minutes > 0:  # Only record if there's actual time
                                # Insert participation record
                                cursor.execute("""
                                    INSERT INTO participation (
                                        event_id, user_id, username, display_name, 
                                        joined_at, left_at, duration_minutes, is_org_member
                                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                """, (
                                    event_id,
                                    user_id,
                                    username,
                                    username,
                                    join_time,
                                    leave_time,
                                    duration_minutes,
                                    is_org_member
                                ))
                                participation_records += 1
                                user_total_time += duration_minutes
                                total_participation_time += duration_minutes
                    
                    # Commit all changes
                    conn.commit()
            
            finally:
                conn.close()
            
            # Calculate stats
            avg_participation = total_participation_time / participants if participants > 0 else 0
            
            return {
                'success': True,
                'event_id': event_id,
                'location': location,
                'event_start': event_start,
                'participation_records': participation_records,
                'total_participation_time': total_participation_time,
                'avg_participation': avg_participation
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


class TestDataDeletionView(ui.View):
    """UI for deleting test data with confirmation."""
    
    def __init__(self):
        super().__init__(timeout=300)
        
        # Add delete button (requires confirmation)
        self.add_item(ConfirmDeleteButton())
        
        # Add cancel button
        self.add_item(CancelDeleteButton())


class ConfirmDeleteButton(ui.Button):
    """Button to confirm test data deletion."""
    
    def __init__(self):
        super().__init__(
            label="⚠️ DELETE ALL TEST DATA",
            style=discord.ButtonStyle.danger,
            emoji="🗑️"
        )
    
    async def callback(self, interaction: discord.Interaction):
        # Show final confirmation modal
        modal = FinalDeleteConfirmationModal()
        await interaction.response.send_modal(modal)


class FinalDeleteConfirmationModal(ui.Modal):
    """Final confirmation modal for deletion."""
    
    def __init__(self):
        super().__init__(title='Confirm Test Data Deletion')
        
        self.confirmation = ui.TextInput(
            label='Type "DELETE" to confirm',
            placeholder='Type DELETE (all caps) to confirm deletion',
            required=True,
            max_length=10
        )
        
        self.add_item(self.confirmation)
    
    async def on_submit(self, interaction: discord.Interaction):
        if self.confirmation.value.upper() != 'DELETE':
            await interaction.response.send_message(
                "❌ Deletion cancelled. You must type 'DELETE' (all caps) to confirm.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            # Perform deletion
            from config.settings import get_database_url
            from database.connection import resolve_database_url
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            db_url = get_database_url()
            if not db_url:
                await interaction.followup.send("❌ Database connection not available", ephemeral=True)
                return
            
            resolved_url = resolve_database_url(db_url)
            conn = psycopg2.connect(resolved_url, cursor_factory=RealDictCursor)
            
            deleted_counts = {}
            
            try:
                with conn.cursor() as cursor:
                    # Delete test participation records (must be first due to foreign keys)
                    try:
                        cursor.execute("""
                            DELETE FROM participation 
                            WHERE (user_id ~ '^[0-9]+$' AND CAST(user_id AS BIGINT) >= 9000000000000000000)
                               OR user_id LIKE 'test_user_%'
                               OR user_id LIKE 'TestMiner%'
                        """)
                        deleted_counts['participation'] = cursor.rowcount
                    except Exception as e:
                        print(f"Error deleting participation: {e}")
                        deleted_counts['participation'] = 0
                    
                    # Delete test payroll records (SM- events with Test in name)
                    try:
                        cursor.execute("""
                            DELETE FROM payrolls 
                            WHERE event_id IN (
                                SELECT event_id FROM events 
                                WHERE event_id LIKE 'sm-%' AND event_name LIKE '%Test%'
                            )
                        """)
                        deleted_counts['payrolls'] = cursor.rowcount
                    except Exception as e:
                        print(f"Error deleting payrolls: {e}")
                        deleted_counts['payrolls'] = 0
                    
                    # Delete test events (SM- events with Test in name)
                    try:
                        cursor.execute("""
                            DELETE FROM events 
                            WHERE event_id LIKE 'sm-%' AND event_name LIKE '%Test%'
                        """)
                        deleted_counts['events'] = cursor.rowcount
                    except Exception as e:
                        print(f"Error deleting events: {e}")
                        deleted_counts['events'] = 0
                    
                    # Delete test users (both numeric and legacy string user IDs)
                    try:
                        cursor.execute("""
                            DELETE FROM users 
                            WHERE (user_id ~ '^[0-9]+$' AND CAST(user_id AS BIGINT) >= 9000000000000000000)
                               OR user_id LIKE 'test_user_%'
                               OR user_id LIKE 'TestMiner%'
                        """)
                        deleted_counts['users'] = cursor.rowcount
                    except Exception as e:
                        print(f"Error deleting users: {e}")
                        deleted_counts['users'] = 0
                    
                    conn.commit()
            
            finally:
                conn.close()
            
            # Create success embed
            embed = discord.Embed(
                title="🗑️ Test Data Deleted",
                description="Successfully removed test mining data from the unified database",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            
            for table, count in deleted_counts.items():
                if count > 0:
                    embed.add_field(
                        name=f"{table.title()} Records",
                        value=f"{count} deleted",
                        inline=True
                    )
            
            total_deleted = sum(deleted_counts.values())
            if total_deleted == 0:
                embed.add_field(
                    name="✅ Already Clean",
                    value="No test data found to delete",
                    inline=False
                )
            else:
                embed.add_field(
                    name="✅ Cleanup Complete",
                    value=f"Removed {total_deleted} total records from database",
                    inline=False
                )
            
            # Disable all buttons in parent view
            original_view = interaction.message.components[0] if interaction.message.components else None
            if original_view:
                for item in original_view.children:
                    item.disabled = True
            
            await interaction.edit_original_response(embed=embed, view=None)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error deleting test data: {str(e)}", ephemeral=True)


class CancelDeleteButton(ui.Button):
    """Button to cancel deletion."""
    
    def __init__(self):
        super().__init__(
            label="Cancel",
            style=discord.ButtonStyle.secondary,
            emoji="❌"
        )
    
    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="❌ Deletion Cancelled",
            description="Test data deletion has been cancelled.",
            color=discord.Color.orange()
        )
        
        # Disable all buttons
        for item in self.view.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self.view)


class TestDataCommands(commands.GroupCog, name="test-data"):
    """Test data generation commands for mining system (Admin only)"""
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="create", description="Create test mining event with dummy participation data")
    @app_commands.default_permissions(administrator=True)
    async def create_test_data(self, interaction: discord.Interaction):
        """Create test mining event with dummy participation data for payroll testing"""
        # Open test data creation modal
        modal = TestDataCreationModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(name="delete", description="Delete all test mining data")
    @app_commands.default_permissions(administrator=True)
    async def delete_test_data(self, interaction: discord.Interaction):
        """Delete all test mining data from the unified database"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # First, scan for existing test data to show what will be deleted
            from config.settings import get_database_url
            from database.connection import resolve_database_url
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            db_url = get_database_url()
            if not db_url:
                await interaction.followup.send("❌ Database connection not available", ephemeral=True)
                return
            
            resolved_url = resolve_database_url(db_url)
            conn = psycopg2.connect(resolved_url, cursor_factory=RealDictCursor)
            
            test_data_summary = {
                'events': [],
                'users': 0,
                'participation': 0,
                'payrolls': 0
            }
            
            try:
                with conn.cursor() as cursor:
                    # Get test events to show (SM- events with Test in name)
                    try:
                        cursor.execute("""
                            SELECT event_id, event_name, location_notes, started_at, status, created_at 
                            FROM events 
                            WHERE event_id LIKE 'sm-%' AND event_name LIKE '%Test%'
                            ORDER BY created_at DESC 
                            LIMIT 10
                        """)
                        test_data_summary['events'] = cursor.fetchall() or []
                    except Exception as e:
                        print(f"Error querying test events: {e}")
                        test_data_summary['events'] = []
                    
                    # Count test users (both numeric test users and string-based legacy users)
                    try:
                        cursor.execute("""
                            SELECT COUNT(*) FROM users 
                            WHERE (user_id ~ '^[0-9]+$' AND CAST(user_id AS BIGINT) >= 9000000000000000000)
                               OR user_id LIKE 'test_user_%'
                               OR user_id LIKE 'TestMiner%'
                        """)
                        result = cursor.fetchone()
                        test_data_summary['users'] = result[0] if result else 0
                    except Exception as e:
                        print(f"Error counting test users: {e}")
                        test_data_summary['users'] = 0
                    
                    # Count participation records (both numeric and legacy string user IDs)
                    try:
                        cursor.execute("""
                            SELECT COUNT(*) FROM participation 
                            WHERE (user_id ~ '^[0-9]+$' AND CAST(user_id AS BIGINT) >= 9000000000000000000)
                               OR user_id LIKE 'test_user_%'
                               OR user_id LIKE 'TestMiner%'
                        """)
                        result = cursor.fetchone()
                        test_data_summary['participation'] = result[0] if result else 0
                    except Exception as e:
                        print(f"Error counting participation records: {e}")
                        test_data_summary['participation'] = 0
                    
                    # Count payroll records
                    try:
                        cursor.execute("""
                            SELECT COUNT(*) FROM payrolls 
                            WHERE event_id IN (
                                SELECT event_id FROM events 
                                WHERE event_id LIKE 'sm-%' AND event_name LIKE '%Test%'
                            )
                        """)
                        result = cursor.fetchone()
                        test_data_summary['payrolls'] = result[0] if result else 0
                    except Exception as e:
                        print(f"Error counting payroll records: {e}")
                        test_data_summary['payrolls'] = 0
            
            finally:
                if conn:
                    conn.close()
            
            # Create enhanced deletion confirmation UI
            embed = discord.Embed(
                title="⚠️ Delete All Test Data",
                description="**WARNING: This action cannot be undone!**\n\n"
                           "The following test data will be permanently deleted:",
                color=discord.Color.red()
            )
            
            # Show test events if any exist
            if test_data_summary['events']:
                event_list = []
                for event in test_data_summary['events'][:5]:  # Show up to 5
                    status_emoji = "🔴" if event['status'] == 'closed' else "🟢"
                    event_list.append(f"{status_emoji} `{event['event_id']}` - {event['event_name']}")
                
                events_text = "\n".join(event_list)
                if len(test_data_summary['events']) > 5:
                    events_text += f"\n... and {len(test_data_summary['events']) - 5} more"
                
                embed.add_field(
                    name=f"🎯 Test Events ({len(test_data_summary['events'])} total)",
                    value=events_text,
                    inline=False
                )
            
            # Show counts
            embed.add_field(
                name="📊 Data Counts",
                value=f"**Events:** {len(test_data_summary['events'])}\n"
                      f"**Test Users:** {test_data_summary['users']}\n" 
                      f"**Participation Records:** {test_data_summary['participation']}\n"
                      f"**Payroll Records:** {test_data_summary['payrolls']}",
                inline=True
            )
            
            total_items = (len(test_data_summary['events']) + test_data_summary['users'] + 
                          test_data_summary['participation'] + test_data_summary['payrolls'])
            
            if total_items == 0:
                embed.add_field(
                    name="✅ No Test Data Found",
                    value="No test data found to delete. Database is already clean.",
                    inline=False
                )
                embed.color = discord.Color.green()
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            else:
                embed.add_field(
                    name="🛑 Confirmation Required",
                    value=f"**Total Items:** {total_items}\n"
                          "Click the deletion button below and type 'DELETE' to confirm.",
                    inline=False
                )
            
            view = TestDataDeletionView()
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            error_msg = str(e) if str(e) else f"Unknown error occurred (type: {type(e).__name__})"
            print(f"Error in delete_test_data scanning: {error_msg}")
            print(f"Exception type: {type(e)}")
            print(f"Exception args: {e.args}")
            
            await interaction.followup.send(
                f"❌ Error scanning test data: {error_msg}", 
                ephemeral=True
            )

    @app_commands.command(name="status", description="Show current test data in database")
    @app_commands.default_permissions(administrator=True)
    async def test_status(self, interaction: discord.Interaction):
        """Show current test data status in the unified database"""
        try:
            from config.settings import get_database_url
            from database.connection import resolve_database_url
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            db_url = get_database_url()
            if not db_url:
                await interaction.response.send_message("❌ Database connection not available", ephemeral=True)
                return
            
            resolved_url = resolve_database_url(db_url)
            conn = psycopg2.connect(resolved_url, cursor_factory=RealDictCursor)
            
            counts = {}
            recent_events = []
            
            try:
                with conn.cursor() as cursor:
                    # Count test users (both numeric and legacy string user IDs)
                    try:
                        cursor.execute("""
                            SELECT COUNT(*) FROM users 
                            WHERE (user_id ~ '^[0-9]+$' AND CAST(user_id AS BIGINT) >= 9000000000000000000)
                               OR user_id LIKE 'test_user_%'
                               OR user_id LIKE 'TestMiner%'
                        """)
                        result = cursor.fetchone()
                        counts['users'] = result[0] if result else 0
                    except Exception as e:
                        print(f"Error counting users: {e}")
                        counts['users'] = 0
                    
                    # Count test events (recent ones created by this command)
                    try:
                        cursor.execute("""
                            SELECT COUNT(*) FROM events 
                            WHERE event_id LIKE 'sm-%' AND event_name LIKE '%Test%' 
                            AND event_type = 'mining'
                        """)
                        result = cursor.fetchone()
                        counts['events'] = result[0] if result else 0
                    except Exception as e:
                        print(f"Error counting events: {e}")
                        counts['events'] = 0
                    
                    # Count test participation (both numeric and legacy string user IDs)
                    try:
                        cursor.execute("""
                            SELECT COUNT(*) FROM participation 
                            WHERE (user_id ~ '^[0-9]+$' AND CAST(user_id AS BIGINT) >= 9000000000000000000)
                               OR user_id LIKE 'test_user_%'
                               OR user_id LIKE 'TestMiner%'
                        """)
                        result = cursor.fetchone()
                        counts['participation'] = result[0] if result else 0
                    except Exception as e:
                        print(f"Error counting participation: {e}")
                        counts['participation'] = 0
                    
                    # Count test payrolls
                    try:
                        cursor.execute("""
                            SELECT COUNT(*) FROM payrolls p
                            JOIN events e ON p.event_id = e.event_id
                            WHERE e.created_at > NOW() - INTERVAL '7 days'
                            AND e.event_type = 'mining'
                        """)
                        result = cursor.fetchone()
                        counts['payrolls'] = result[0] if result else 0
                    except Exception as e:
                        print(f"Error counting payrolls: {e}")
                        counts['payrolls'] = 0
                    
                    # Get recent test events
                    try:
                        cursor.execute("""
                            SELECT event_id, location_notes, started_at, ended_at, status, created_at 
                            FROM events 
                            WHERE event_id LIKE 'sm-%' AND event_name LIKE '%Test%' 
                            AND event_type = 'mining'
                            ORDER BY created_at DESC 
                            LIMIT 5
                        """)
                        recent_events = cursor.fetchall()
                    except Exception as e:
                        print(f"Error fetching recent events: {e}")
                        recent_events = []
            
            finally:
                conn.close()
            
            # Create status embed
            embed = discord.Embed(
                title="🧪 Test Data Status",
                description="Current test data in the unified mining database",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(name="Test Users", value=f"{counts['users']}", inline=True)
            embed.add_field(name="Test Events", value=f"{counts['events']}", inline=True)  
            embed.add_field(name="Participation Records", value=f"{counts['participation']}", inline=True)
            embed.add_field(name="Payroll Records", value=f"{counts['payrolls']}", inline=True)
            
            if recent_events:
                event_list = []
                for event in recent_events[:3]:  # Show max 3 events
                    status_emoji = "🔴" if event['status'] == 'closed' else "🟢"
                    event_list.append(f"{status_emoji} `{event['event_id']}` - {event['location_notes']}")
                
                embed.add_field(
                    name="Recent Test Events",
                    value="\n".join(event_list) if event_list else "None",
                    inline=False
                )
            
            if any(counts.values()):
                embed.add_field(
                    name="⚠️ Cleanup Available",
                    value="Use `/test-data delete` to remove test data",
                    inline=False
                )
            else:
                embed.add_field(
                    name="✅ Database Clean",
                    value="No test data found in database",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error checking test status: {str(e)}", ephemeral=True)
            import traceback
            print(f"Test status error: {traceback.format_exc()}")

async def setup(bot):
    """Setup function for discord.py extension loading."""
    await bot.add_cog(TestDataCommands(bot))
    print("✅ Test Data commands loaded")