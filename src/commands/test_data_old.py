"""
Test data generation command for the unified mining system.
Creates dummy events and participation data for testing the payroll module.
"""

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import random
import string
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

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
        try:
            await interaction.response.defer()
            
            # Validate parameters
            if not (1 <= participants <= 50):
                await interaction.followup.send("❌ Participants must be between 1 and 50", ephemeral=True)
                return
            
            if not (0 <= hours_ago <= 48):
                await interaction.followup.send("❌ Hours ago must be between 0 and 48", ephemeral=True)
                return
            
            # Import required modules
            from config.settings import get_database_url
            from database.connection import resolve_database_url
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            db_url = get_database_url()
            if not db_url:
                await interaction.followup.send("❌ Database connection not available", ephemeral=True)
                return
            
            # Generate event ID
            random_part = ''.join(random.choices('0123456789', k=5))
            event_id = f"sm-{random_part}"
            
            # Calculate event times
            event_start = datetime.now() - timedelta(hours=hours_ago)
            event_end = event_start + timedelta(hours=random.randint(2, 6))  # 2-6 hour session
            
            location = location or random.choice([
                "Daymar", "Yela", "Aberdeen", "Magda", "Arial", "Lyria", 
                "Wala", "Cellin", "Hurston", "ArcCorp"
            ])
            
            # Connect to database
            resolved_url = resolve_database_url(db_url)
            conn = psycopg2.connect(resolved_url, cursor_factory=RealDictCursor)
            
            try:
                with conn.cursor() as cursor:
                    # Create test event in unified events table
                    cursor.execute("""
                        INSERT INTO events (
                            event_id, guild_id, event_type, event_name, organizer_id, organizer_name,
                            started_at, ended_at, status, location_notes, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (event_id) DO NOTHING
                    """, (
                        event_id,
                        str(interaction.guild.id),
                        'mining',
                        f'Test Mining Event at {location}',
                        str(interaction.user.id),
                        interaction.user.display_name,
                        event_start,
                        event_end,
                        'closed',  # Mark as closed so payroll can be calculated
                        location,
                        datetime.now()
                    ))
                    
                    # Create test participants and participation records
                    test_users_created = 0
                    participation_records = 0
                    total_participation_time = 0
                    
                    for i in range(participants):
                        # Generate test user ID (numeric for BIGINT field)
                        # Use a safe range starting from 9000000000000000000 to avoid conflicts
                        base_test_id = 9000000000000000000
                        # Extract numeric part from event_id (e.g., "sm-12345" -> "12345")
                        try:
                            event_numeric_part = event_id.split('-')[1] if '-' in event_id else event_id
                            event_number = int(event_numeric_part)
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
            
            # Calculate stats for display
            avg_participation = total_participation_time / participants if participants > 0 else 0
            org_members = sum(1 for i in range(participants) if random.choice([True, False]))
            
            # Create success embed
            embed = discord.Embed(
                title="✅ Test Mining Event Created",
                description=f"Successfully created test event `{event_id}` with dummy participation data",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            embed.add_field(name="Event ID", value=f"`{event_id}`", inline=True)
            embed.add_field(name="Location", value=location, inline=True)
            embed.add_field(name="Status", value="Closed (Ready for payroll)", inline=True)
            
            embed.add_field(name="Event Start", value=f"<t:{int(event_start.timestamp())}:R>", inline=True)
            embed.add_field(name="Event Duration", value=f"{(event_end - event_start).total_seconds() / 3600:.1f} hours", inline=True)
            embed.add_field(name="Participants", value=f"{participants}", inline=True)
            
            embed.add_field(name="Participation Records", value=f"{participation_records}", inline=True)
            embed.add_field(name="Total Participation Time", value=f"{total_participation_time:,} minutes", inline=True)
            embed.add_field(name="Avg Time per Participant", value=f"{avg_participation:.1f} minutes", inline=True)
            
            embed.add_field(
                name="🧪 Testing Commands",
                value=f"• Use `/payroll mining` with event ID `{event_id}`\\n"
                      f"• Use `/mining status` to see event details\\n"
                      f"• Use `/test-data delete` when done testing",
                inline=False
            )
            
            embed.set_footer(text="⚠️ Remember to clean up test data when finished!")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_msg = f"❌ Error creating test data: {str(e)}"
            await interaction.followup.send(error_msg, ephemeral=True)
            import traceback
            print(f"Test data creation error: {traceback.format_exc()}")

    @app_commands.command(name="delete", description="Delete all test mining data")
    @app_commands.describe(
        confirm="Type 'DELETE' to confirm deletion of all test data"
    )
    @app_commands.default_permissions(administrator=True)
    async def delete_test_data(self, interaction: discord.Interaction, confirm: str):
        """Delete all test mining data from the unified database"""
        try:
            if confirm.upper() != 'DELETE':
                await interaction.response.send_message(
                    "❌ Please type 'DELETE' to confirm deletion of test data",
                    ephemeral=True
                )
                return
            
            await interaction.response.defer()
            
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
                            WHERE user_id >= 9000000000000000000
                        """)
                        deleted_counts['participation'] = cursor.rowcount
                    except Exception as e:
                        await interaction.followup.send(f"❌ Error deleting participation records: {e}", ephemeral=True)
                        return
                    
                    # Delete test payroll records
                    try:
                        cursor.execute("""
                            DELETE FROM payrolls 
                            WHERE event_id LIKE 'sm-%' 
                            AND event_id IN (
                                SELECT event_id FROM events 
                                WHERE organizer_id = %s OR location_notes LIKE '%Test%'
                            )
                        """, (str(interaction.user.id),))
                        deleted_counts['payrolls'] = cursor.rowcount
                    except Exception as e:
                        await interaction.followup.send(f"❌ Error deleting payroll records: {e}", ephemeral=True)
                        return
                    
                    # Delete test events (look for events created by this command or with test characteristics)
                    try:
                        cursor.execute("""
                            DELETE FROM events 
                            WHERE event_id LIKE 'sm-%' 
                            AND (organizer_id = %s OR location_notes IN (
                                'Daymar', 'Yela', 'Aberdeen', 'Magda', 'Arial', 'Lyria', 
                                'Wala', 'Cellin', 'Hurston', 'ArcCorp'
                            ))
                            AND created_at > NOW() - INTERVAL '7 days'
                        """, (str(interaction.user.id),))
                        deleted_counts['events'] = cursor.rowcount
                    except Exception as e:
                        await interaction.followup.send(f"❌ Error deleting event records: {e}", ephemeral=True)
                        return
                    
                    # Delete test users
                    try:
                        cursor.execute("""
                            DELETE FROM users 
                            WHERE user_id >= 9000000000000000000
                        """)
                        deleted_counts['users'] = cursor.rowcount
                    except Exception as e:
                        await interaction.followup.send(f"❌ Error deleting user records: {e}", ephemeral=True)
                        return
                    
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
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error deleting test data: {str(e)}", ephemeral=True)
            import traceback
            print(f"Test data deletion error: {traceback.format_exc()}")

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
                    # Count test users
                    cursor.execute("SELECT COUNT(*) FROM users WHERE user_id >= 9000000000000000000")
                    counts['users'] = cursor.fetchone()[0]
                    
                    # Count test events (recent ones created by this command)
                    cursor.execute("""
                        SELECT COUNT(*) FROM events 
                        WHERE event_id LIKE 'sm-%' 
                        AND created_at > NOW() - INTERVAL '7 days'
                        AND event_type = 'mining'
                    """)
                    counts['events'] = cursor.fetchone()[0]
                    
                    # Count test participation
                    cursor.execute("SELECT COUNT(*) FROM participation WHERE user_id >= 9000000000000000000")
                    counts['participation'] = cursor.fetchone()[0]
                    
                    # Count test payrolls
                    cursor.execute("""
                        SELECT COUNT(*) FROM payrolls p
                        JOIN events e ON p.event_id = e.event_id
                        WHERE e.created_at > NOW() - INTERVAL '7 days'
                        AND e.event_type = 'mining'
                    """)
                    counts['payrolls'] = cursor.fetchone()[0]
                    
                    # Get recent test events
                    cursor.execute("""
                        SELECT event_id, location, start_time, end_time, status, created_at 
                        FROM events 
                        WHERE event_id LIKE 'sm-%' 
                        AND created_at > NOW() - INTERVAL '7 days'
                        AND event_type = 'mining'
                        ORDER BY created_at DESC 
                        LIMIT 5
                    """)
                    recent_events = cursor.fetchall()
            
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
                    event_list.append(f"{status_emoji} `{event['event_id']}` - {event['location']}")
                
                embed.add_field(
                    name="Recent Test Events",
                    value="\\n".join(event_list) if event_list else "None",
                    inline=False
                )
            
            if any(counts.values()):
                embed.add_field(
                    name="⚠️ Cleanup Available",
                    value="Use `/test-data delete DELETE` to remove test data",
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