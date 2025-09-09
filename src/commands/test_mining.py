"""
Temporary test command for Sunday Mining system
Creates and deletes test data for end-to-end testing
"""

import discord
from discord import app_commands
from datetime import datetime, date, timedelta
import random

class TestMiningCommands(app_commands.Group):
    """Test commands for Sunday Mining system"""
    
    def __init__(self):
        super().__init__(name='redtestmining', description='Generate test data for Sunday Mining (Admin only)')
    
    @app_commands.command(name="create", description="Create test mining session data (Admin only)")
    @app_commands.describe(
        participants="Number of test participants (1-20)",
        hours_ago="How many hours ago the session started (0-24)"
    )
    @app_commands.default_permissions(administrator=True)
    async def create_test_data(self, interaction: discord.Interaction, participants: int = 5, hours_ago: int = 2):
        """Create test mining session data"""
        try:
            from config.settings import get_database_url, get_sunday_mining_channels
            from database.operations import create_mining_event, save_mining_participation
            from database.connection import resolve_database_url
            import psycopg2
            from urllib.parse import urlparse
            
            await interaction.response.defer()
            
            # Validate parameters
            if not (1 <= participants <= 20):
                await interaction.followup.send("❌ Participants must be between 1 and 20", ephemeral=True)
                return
            
            if not (0 <= hours_ago <= 24):
                await interaction.followup.send("❌ Hours ago must be between 0 and 24", ephemeral=True)
                return
            
            db_url = get_database_url()
            if not db_url:
                await interaction.followup.send("❌ Database connection not available", ephemeral=True)
                return
            
            # Create test mining event
            event_date = date.today() - timedelta(days=(1 if hours_ago > 12 else 0))
            event_name = f"TEST Sunday Mining - {event_date.strftime('%Y-%m-%d')}"
            
            event_id = create_mining_event(
                db_url,
                interaction.guild.id,
                event_date,
                event_name
            )
            
            if not event_id:
                await interaction.followup.send("❌ Failed to create test mining event", ephemeral=True)
                return
            
            # Get mining channels for this guild
            mining_channels = get_sunday_mining_channels(interaction.guild.id)
            channel_ids = list(mining_channels.values())
            
            if not channel_ids:
                # Create some default test mining channels
                default_channels = ['alpha', 'bravo', 'charlie', 'delta']
                channel_ids = [f'test_channel_{i}' for i in range(len(default_channels))]
                
                # Add test channels to database using resolved URL
                resolved_url = resolve_database_url(db_url)
                conn = psycopg2.connect(resolved_url)
                
                with conn.cursor() as cursor:
                    for i, channel_name in enumerate(default_channels):
                        cursor.execute("""
                            INSERT INTO mining_channels (guild_id, channel_id, channel_name, description, is_active)
                            VALUES (%s, %s, %s, %s, true)
                            ON CONFLICT (guild_id, channel_id) DO NOTHING
                        """, (
                            str(interaction.guild.id),
                            channel_ids[i],
                            f"Test Mining {channel_name.title()}",
                            f"Test channel for {channel_name} mining team"
                        ))
                    conn.commit()
                conn.close()
                
                print(f"✅ Created {len(channel_ids)} test mining channels")
            
            # Generate test users and participation data
            test_users = []
            base_time = datetime.now() - timedelta(hours=hours_ago)
            
            # Create test users in database first using resolved URL
            resolved_url = resolve_database_url(db_url)
            conn = psycopg2.connect(resolved_url)
            
            with conn.cursor() as cursor:
                for i in range(participants):
                    test_user = {
                        'user_id': f'test_user_{i+1}_{event_id}',
                        'username': f'TestMiner{i+1}',
                        'is_org_member': random.choice([True, False])
                    }
                    test_users.append(test_user)
                    
                    # Insert test user
                    cursor.execute("""
                        INSERT INTO users (user_id, username, display_name, first_seen, last_seen)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (user_id) DO NOTHING
                    """, (
                        test_user['user_id'],
                        test_user['username'],
                        test_user['username'],
                        base_time,
                        base_time + timedelta(hours=2)
                    ))
                    
                    # Add guild membership
                    cursor.execute("""
                        INSERT INTO guild_memberships (guild_id, user_id, is_org_member, joined_at)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (guild_id, user_id) DO NOTHING
                    """, (
                        str(interaction.guild.id),
                        test_user['user_id'],
                        test_user['is_org_member'],
                        base_time
                    ))
                
                conn.commit()
            conn.close()
            
            # Generate participation data
            successful_saves = 0
            for user in test_users:
                # Generate 1-3 participation sessions per user
                num_sessions = random.randint(1, 3)
                
                for session in range(num_sessions):
                    # Random participation duration (30 minutes to 3 hours)
                    duration_minutes = random.randint(30, 180)
                    
                    # Random channel
                    channel_id = random.choice(channel_ids)
                    
                    # Calculate times with some spread
                    session_start_offset = session * 60 + random.randint(0, 30)  # Each session starts later
                    join_time = base_time + timedelta(minutes=session_start_offset)
                    leave_time = join_time + timedelta(minutes=duration_minutes)
                    
                    # Save participation
                    success = save_mining_participation(
                        db_url,
                        event_id,
                        user['user_id'],
                        user['username'],
                        channel_id,
                        f"Mining Channel {channel_id}",
                        join_time,
                        leave_time,
                        duration_minutes,
                        user['is_org_member']
                    )
                    
                    if success:
                        successful_saves += 1
            
            # Create success embed
            embed = discord.Embed(
                title="✅ Test Mining Data Created",
                description=f"Successfully created test data for Sunday Mining system",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            embed.add_field(name="Event ID", value=f"`{event_id}`", inline=True)
            embed.add_field(name="Event Name", value=event_name, inline=True)
            embed.add_field(name="Event Date", value=event_date.strftime("%Y-%m-%d"), inline=True)
            
            embed.add_field(name="Test Users Created", value=f"{participants}", inline=True)
            embed.add_field(name="Participation Records", value=f"{successful_saves}", inline=True)
            embed.add_field(name="Session Started", value=f"{hours_ago} hours ago", inline=True)
            
            org_members = sum(1 for u in test_users if u['is_org_member'])
            embed.add_field(name="Org Members", value=f"{org_members}/{participants}", inline=True)
            
            embed.add_field(
                name="🧪 Testing Instructions",
                value="• Use `/redpayroll calculate` to test payroll\n"
                      "• Use `/redpricecheck ores` to get current prices\n"
                      "• Use `/redtestmining delete` when done testing",
                inline=False
            )
            
            embed.set_footer(text="⚠️ Remember to delete test data when finished!")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error creating test data: {str(e)}")
            import traceback
            print(f"Test data creation error: {traceback.format_exc()}")
    
    @app_commands.command(name="delete", description="Delete all test mining data (Admin only)")
    @app_commands.describe(
        confirm="Type 'DELETE' to confirm deletion of all test data"
    )
    @app_commands.default_permissions(administrator=True)
    async def delete_test_data(self, interaction: discord.Interaction, confirm: str):
        """Delete all test mining data"""
        try:
            if confirm.upper() != 'DELETE':
                await interaction.response.send_message(
                    "❌ Please type 'DELETE' to confirm deletion of test data",
                    ephemeral=True
                )
                return
            
            from config.settings import get_database_url
            from database.connection import resolve_database_url
            import psycopg2
            from urllib.parse import urlparse
            
            await interaction.response.defer()
            
            db_url = get_database_url()
            if not db_url:
                await interaction.followup.send("❌ Database connection not available", ephemeral=True)
                return
            
            resolved_url = resolve_database_url(db_url)
            conn = psycopg2.connect(resolved_url)
            
            deleted_counts = {}
            
            with conn.cursor() as cursor:
                # Delete test participation records
                cursor.execute("""
                    DELETE FROM mining_participation 
                    WHERE user_id LIKE 'test_user_%'
                """)
                deleted_counts['participation'] = cursor.rowcount
                
                # Delete test mining events
                cursor.execute("""
                    DELETE FROM mining_events 
                    WHERE name LIKE 'TEST Sunday Mining%'
                """)
                deleted_counts['events'] = cursor.rowcount
                
                # Delete test guild memberships
                cursor.execute("""
                    DELETE FROM guild_memberships 
                    WHERE user_id LIKE 'test_user_%'
                """)
                deleted_counts['memberships'] = cursor.rowcount
                
                # Delete test mining channels
                cursor.execute("""
                    DELETE FROM mining_channels 
                    WHERE channel_id LIKE 'test_channel_%'
                """)
                deleted_counts['channels'] = cursor.rowcount
                
                # Delete test users
                cursor.execute("""
                    DELETE FROM users 
                    WHERE user_id LIKE 'test_user_%'
                """)
                deleted_counts['users'] = cursor.rowcount
                
                conn.commit()
            
            conn.close()
            
            # Create success embed
            embed = discord.Embed(
                title="🗑️ Test Data Deleted",
                description="Successfully removed all test mining data from the database",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            
            for table, count in deleted_counts.items():
                embed.add_field(
                    name=f"{table.title()} Deleted",
                    value=f"{count} records",
                    inline=True
                )
            
            embed.add_field(
                name="✅ Cleanup Complete",
                value="Database is now clean of test data",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error deleting test data: {str(e)}")
            import traceback
            print(f"Test data deletion error: {traceback.format_exc()}")
    
    @app_commands.command(name="status", description="Show current test data status (Admin only)")
    @app_commands.default_permissions(administrator=True)
    async def test_status(self, interaction: discord.Interaction):
        """Show current test data status"""
        try:
            from config.settings import get_database_url
            from database.connection import resolve_database_url
            import psycopg2
            from urllib.parse import urlparse
            
            db_url = get_database_url()
            if not db_url:
                await interaction.response.send_message("❌ Database connection not available", ephemeral=True)
                return
            
            resolved_url = resolve_database_url(db_url)
            conn = psycopg2.connect(resolved_url)
            
            counts = {}
            
            with conn.cursor() as cursor:
                # Count test users
                cursor.execute("SELECT COUNT(*) FROM users WHERE user_id LIKE 'test_user_%'")
                counts['users'] = cursor.fetchone()[0]
                
                # Count test events
                cursor.execute("SELECT COUNT(*) FROM mining_events WHERE name LIKE 'TEST Sunday Mining%'")
                counts['events'] = cursor.fetchone()[0]
                
                # Count test participation
                cursor.execute("SELECT COUNT(*) FROM mining_participation WHERE user_id LIKE 'test_user_%'")
                counts['participation'] = cursor.fetchone()[0]
                
                # Count test mining channels
                cursor.execute("SELECT COUNT(*) FROM mining_channels WHERE channel_id LIKE 'test_channel_%'")
                counts['channels'] = cursor.fetchone()[0]
                
                # Get recent test events
                cursor.execute("""
                    SELECT event_id, name, event_date, created_at 
                    FROM mining_events 
                    WHERE name LIKE 'TEST Sunday Mining%' 
                    ORDER BY created_at DESC 
                    LIMIT 3
                """)
                recent_events = cursor.fetchall()
            
            conn.close()
            
            # Create status embed
            embed = discord.Embed(
                title="🧪 Test Data Status",
                description="Current test data in the database",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(name="Test Users", value=f"{counts['users']}", inline=True)
            embed.add_field(name="Test Events", value=f"{counts['events']}", inline=True)  
            embed.add_field(name="Participation Records", value=f"{counts['participation']}", inline=True)
            embed.add_field(name="Test Channels", value=f"{counts['channels']}", inline=True)
            
            if recent_events:
                event_list = []
                for event_id, name, event_date, created_at in recent_events:
                    event_list.append(f"• `{event_id}` - {name}")
                
                embed.add_field(
                    name="Recent Test Events",
                    value="\n".join(event_list) if event_list else "None",
                    inline=False
                )
            
            if any(counts.values()):
                embed.add_field(
                    name="⚠️ Cleanup Required",
                    value="Use `/redtestmining delete DELETE` to remove test data",
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
    bot.tree.add_command(TestMiningCommands())
    print("✅ Test Mining commands loaded")