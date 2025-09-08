"""
Administrative commands for the Red Legion Discord bot.

This module contains commands for bot administration and configuration management.
"""

import discord
from datetime import datetime, timedelta
import os
import sys
import random
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.decorators import admin_only, error_handler


def register_commands(bot):
    """Register all administrative commands with the bot."""
    
    @bot.command(name="refresh_config")
    @admin_only()
    @error_handler
    async def refresh_config(ctx):
        """Refresh bot configuration from Secret Manager"""
        try:
            embed = discord.Embed(
                title="🔄 Configuration Refresh",
                description="Refreshing configuration from Secret Manager...",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            # Send initial message
            msg = await ctx.send(embed=embed)
            
            # Attempt to refresh configuration
            try:
                from config.settings import get_config
                
                # Get fresh config
                new_config = get_config()
                
                # Update embed with success
                embed.title = "✅ Configuration Refreshed"
                embed.description = "Configuration successfully refreshed from Secret Manager"
                embed.color = discord.Color.green()
                
                # Add status fields
                embed.add_field(
                    name="Database URL", 
                    value="✅ Updated" if new_config.get('DATABASE_URL') else "❌ Not found", 
                    inline=True
                )
                embed.add_field(
                    name="Discord Token", 
                    value="✅ Available" if new_config.get('DISCORD_TOKEN') else "❌ Not found", 
                    inline=True
                )
                
                await msg.edit(embed=embed)
                
            except Exception as config_error:
                embed.title = "❌ Configuration Refresh Failed"
                embed.description = f"Failed to refresh configuration: {str(config_error)}"
                embed.color = discord.Color.red()
                embed.add_field(
                    name="Error Details",
                    value=str(config_error)[:100],
                    inline=False
                )
                await msg.edit(embed=embed)
                
        except Exception as e:
            await ctx.send(f"❌ Failed to refresh configuration: {str(e)}")

    @bot.command(name="restart_red_legion_bot")
    @admin_only()
    @error_handler
    async def restart_bot(ctx):
        """Restart the bot process (admin only)"""
        try:
            # Create confirmation embed
            embed = discord.Embed(
                title="🔄 Bot Restart Initiated",
                description="Restarting the Red Legion bot...",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            embed.add_field(
                name="Initiated By",
                value=f"{ctx.author.mention} ({ctx.author.id})",
                inline=False
            )
            embed.add_field(
                name="Status",
                value="Bot will restart momentarily",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
            # Give time for the message to send before restarting
            import asyncio
            await asyncio.sleep(2)
            
            # Log the restart
            print(f"Bot restart initiated by {ctx.author} ({ctx.author.id})")
            
            # Restart the bot process
            os.execv(sys.executable, ['python'] + sys.argv)
            
        except Exception as e:
            await ctx.send(f"❌ Failed to restart bot: {str(e)}")

    @bot.command(name="add_mining_channel")
    @admin_only()
    @error_handler
    async def add_mining_channel(ctx, channel: discord.VoiceChannel, *, description=None):
        """Add a voice channel to Sunday mining tracking"""
        try:
            from database.operations import add_mining_channel
            from config.settings import get_database_url
            
            db_url = get_database_url()
            if not db_url:
                await ctx.send("❌ Database connection not available")
                return
            
            # Add channel to database with guild context
            add_mining_channel(db_url, ctx.guild.id, channel.id, channel.name, description)
            
            embed = discord.Embed(
                title="✅ Mining Channel Added",
                description=f"Successfully added {channel.mention} to Sunday mining tracking",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Channel Name", value=channel.name, inline=True)
            embed.add_field(name="Channel ID", value=str(channel.id), inline=True)
            if description:
                embed.add_field(name="Description", value=description, inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error adding mining channel: {str(e)}")

    @bot.command(name="remove_mining_channel")
    @admin_only()
    @error_handler
    async def remove_mining_channel(ctx, channel: discord.VoiceChannel):
        """Remove a voice channel from Sunday mining tracking"""
        try:
            from database.operations import remove_mining_channel
            from config.settings import get_database_url
            
            db_url = get_database_url()
            if not db_url:
                await ctx.send("❌ Database connection not available")
                return
            
            # Remove channel from database with guild context
            success = remove_mining_channel(db_url, ctx.guild.id, channel.id)
            
            if success:
                embed = discord.Embed(
                    title="✅ Mining Channel Removed",
                    description=f"Successfully removed {channel.mention} from Sunday mining tracking",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                embed.add_field(name="Channel Name", value=channel.name, inline=True)
                embed.add_field(name="Channel ID", value=str(channel.id), inline=True)
            else:
                embed = discord.Embed(
                    title="⚠️ Channel Not Found",
                    description=f"{channel.mention} was not found in mining channel list",
                    color=discord.Color.orange()
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error removing mining channel: {str(e)}")

    @bot.command(name="list_mining_channels")
    @admin_only()
    @error_handler
    async def list_mining_channels(ctx):
        """List all Sunday mining channels"""
        try:
            from database.operations import get_mining_channels
            from config.settings import get_database_url, SUNDAY_MINING_CHANNELS_FALLBACK
            
            db_url = get_database_url()
            if not db_url:
                await ctx.send("❌ Database connection not available")
                return
            
            # Get channels from database for this guild
            channels = get_mining_channels(db_url, ctx.guild.id, active_only=True)
            
            # If no channels in database, use hardcoded fallback
            if not channels:
                # Convert fallback channels to the expected format: (channel_id, channel_name, description, created_at)
                channel_descriptions = {
                    'dispatch': 'Main coordination channel for Sunday mining operations',
                    'alpha': 'Alpha squad mining operations',
                    'bravo': 'Bravo squad mining operations',
                    'charlie': 'Charlie squad mining operations',
                    'delta': 'Delta squad mining operations',
                    'echo': 'Echo squad mining operations',
                    'foxtrot': 'Foxtrot squad mining operations'
                }
                channels = [
                    (channel_id, channel_name.title(), channel_descriptions.get(channel_name, f"{channel_name.title()} mining channel"), "Hardcoded")
                    for channel_name, channel_id in SUNDAY_MINING_CHANNELS_FALLBACK.items()
                ]
            
            embed = discord.Embed(
                title="🎤 Sunday Mining Channels",
                description=f"Currently tracking {len(channels)} voice channels" + (" (using fallback configuration)" if not get_mining_channels(db_url, ctx.guild.id, active_only=True) else ""),
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            if channels:
                channel_list = []
                for channel_id, channel_name, description, created_at in channels:
                    # Try to get the actual Discord channel
                    discord_channel = bot.get_channel(int(channel_id))
                    if discord_channel:
                        channel_info = f"<#{channel_id}> ({channel_name})"
                    else:
                        channel_info = f"#{channel_name} (ID: {channel_id}) *[Channel not found]*"
                    
                    if description:
                        channel_info += f"\n   └ {description}"
                    
                    channel_list.append(channel_info)
                
                # Split into multiple fields if too long
                channel_text = "\n".join(channel_list)
                if len(channel_text) <= 1024:
                    embed.add_field(
                        name="Active Channels",
                        value=channel_text,
                        inline=False
                    )
                else:
                    # Split into chunks
                    chunks = []
                    current_chunk = []
                    current_length = 0
                    
                    for channel in channel_list:
                        if current_length + len(channel) + 1 > 1024:
                            chunks.append("\n".join(current_chunk))
                            current_chunk = [channel]
                            current_length = len(channel)
                        else:
                            current_chunk.append(channel)
                            current_length += len(channel) + 1
                    
                    if current_chunk:
                        chunks.append("\n".join(current_chunk))
                    
                    for i, chunk in enumerate(chunks):
                        embed.add_field(
                            name=f"Active Channels ({i+1}/{len(chunks)})",
                            value=chunk,
                            inline=False
                        )
            else:
                embed.add_field(
                    name="No Channels",
                    value="No mining channels configured. Use `!add_mining_channel` to add channels.",
                    inline=False
                )
            
            # Update footer message based on whether we're using fallback channels
            is_using_fallback = not get_mining_channels(db_url, ctx.guild.id, active_only=True)
            footer_text = "Use !add_mining_channel <channel> [description] to add channels"
            if is_using_fallback:
                footer_text = "Showing hardcoded fallback channels. " + footer_text
            
            embed.set_footer(text=footer_text)
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error listing mining channels: {str(e)}")

    @bot.tree.command(name="testdata", description="Manage test data for mining system (Admin only)")
    @discord.app_commands.describe(
        action="Choose test data action"
    )
    @discord.app_commands.choices(action=[
        discord.app_commands.Choice(name="Create Full Test Dataset", value="create"),
        discord.app_commands.Choice(name="Show Current Test Data", value="show"),
        discord.app_commands.Choice(name="Clean Up All Test Data", value="cleanup")
    ])
    @error_handler
    async def manage_test_data(interaction: discord.Interaction, action: str):
        """Manage test data for mining system testing."""
        
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Access denied. Only administrators can manage test data.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            from config.settings import get_database_url
            import psycopg2
            
            # Get database connection
            db_url = get_database_url()
            if not db_url:
                await interaction.followup.send(
                    "❌ Database connection not available",
                    ephemeral=True
                )
                return
            
            # Test data configuration
            test_guild_id = interaction.guild.id
            test_channels = {
                'Mining Alpha': 111111111111111111,
                'Mining Beta': 222222222222222222,  
                'Mining Gamma': 333333333333333333,
                'Mining Delta': 444444444444444444
            }
            
            test_participants = [
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
            
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            if action == "create":
                await _create_test_data(interaction, cursor, conn, test_guild_id, test_channels, test_participants)
            elif action == "show":
                await _show_test_data(interaction, cursor, test_guild_id)
            elif action == "cleanup":
                await _cleanup_test_data(interaction, cursor, conn, test_guild_id)
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error managing test data: {str(e)}",
                ephemeral=True
            )

async def _create_test_data(interaction, cursor, conn, guild_id, test_channels, test_participants):
    """Create comprehensive test data for mining events and participation."""
    try:
        # First, check if the events table has the required 'id' column
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'events' AND column_name = 'id' AND table_schema = 'public'
        """)
        
        has_id_column = cursor.fetchone() is not None
        
        if not has_id_column:
            # Try to run migration to fix the schema
            await interaction.followup.send(
                "🔧 Events table missing 'id' column, attempting schema migration...",
                ephemeral=True
            )
            
            from database.operations import migrate_schema
            migrate_schema(cursor)
            
            # Check again after migration
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'events' AND column_name = 'id' AND table_schema = 'public'
            """)
            has_id_column = cursor.fetchone() is not None
            
            if not has_id_column:
                raise Exception("Events table schema migration failed - 'id' column still missing. Database may need manual intervention.")
        
        created_data = {'events': [], 'participants': [], 'channels': []}
        
        # Create test channels
        for name, channel_id in test_channels.items():
            cursor.execute("""
                INSERT INTO mining_channels (guild_id, channel_id, channel_name, created_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (guild_id, channel_id) DO NOTHING
            """, (guild_id, channel_id, name, datetime.now()))
            created_data['channels'].append((guild_id, channel_id))
        
        # Create test events with different states
        today = datetime.now().date()
        
        # Event 1: Open event (current)
        event1_time = datetime.combine(today, datetime.min.time().replace(hour=14))
        cursor.execute("""
            INSERT INTO events (guild_id, event_date, event_time, total_participants, 
                              total_payout, is_open, payroll_calculated, pdf_generated)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (guild_id, today, event1_time, 10, None, True, False, False))
        event1_id = cursor.fetchone()[0]
        created_data['events'].append(event1_id)
        
        # Event 2: Completed event (last week)
        event2_date = today - timedelta(days=7)
        event2_time = datetime.combine(event2_date, datetime.min.time().replace(hour=14))
        cursor.execute("""
            INSERT INTO events (guild_id, event_date, event_time, total_participants, 
                              total_payout, is_open, payroll_calculated, pdf_generated)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (guild_id, event2_date, event2_time, 8, 1500000, False, True, True))
        event2_id = cursor.fetchone()[0]
        created_data['events'].append(event2_id)
        
        # Event 3: Payroll done, no PDF
        event3_date = today - timedelta(days=14)
        event3_time = datetime.combine(event3_date, datetime.min.time().replace(hour=14))
        cursor.execute("""
            INSERT INTO events (guild_id, event_date, event_time, total_participants, 
                              total_payout, is_open, payroll_calculated, pdf_generated)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (guild_id, event3_date, event3_time, 12, 2100000, False, True, False))
        event3_id = cursor.fetchone()[0]
        created_data['events'].append(event3_id)
        
        # Create participants for each event
        import random
        for event_id, event_date in [(event1_id, today), (event2_id, event2_date), (event3_id, event3_date)]:
            num_participants = random.randint(8, 12)
            selected = random.sample(test_participants, num_participants)
            
            for participant in selected:
                num_sessions = random.randint(1, 3)
                
                for session in range(num_sessions):
                    channel_name, channel_id = random.choice(list(test_channels.items()))
                    duration = random.randint(1800, 10800)  # 30min to 3h
                    
                    start_offset = random.randint(0, 1800) + (session * 1800)
                    start_time = datetime.combine(event_date, datetime.min.time().replace(hour=14)) + timedelta(seconds=start_offset)
                    end_time = start_time + timedelta(seconds=duration)
                    
                    cursor.execute("""
                        INSERT INTO mining_participation 
                        (event_id, member_id, username, channel_id, start_time, end_time, 
                         duration_seconds, is_org_member, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        event_id, participant['id'], participant['username'], channel_id,
                        start_time, end_time, duration, participant['org'], datetime.now()
                    ))
                    
                    part_id = cursor.fetchone()[0]
                    created_data['participants'].append(part_id)
        
        conn.commit()
        
        # Send success message
        embed = discord.Embed(
            title="🧪 Test Data Created Successfully",
            description="Comprehensive test data has been added to the database",
            color=0x00ff88,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📊 Created Data",
            value=f"• **{len(created_data['events'])}** mining events\n"
                  f"• **{len(created_data['participants'])}** participation records\n"
                  f"• **{len(created_data['channels'])}** test channels",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Event Types",
            value="• Open event (current session)\n"
                  "• Completed event with payroll\n"
                  "• Event with payroll but no PDF",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        conn.rollback()
        raise e

async def _show_test_data(interaction, cursor, guild_id):
    """Show current test data status."""
    try:
        # Get events
        cursor.execute("""
            SELECT id, event_date, total_participants, total_payout, 
                   is_open, payroll_calculated, pdf_generated
            FROM events WHERE guild_id = %s ORDER BY event_date DESC LIMIT 10
        """, (guild_id,))
        events = cursor.fetchall()
        
        # Get participant count
        cursor.execute("""
            SELECT COUNT(*) FROM mining_participation mp
            JOIN events e ON mp.event_id = e.id
            WHERE e.guild_id = %s
        """, (guild_id,))
        participant_count = cursor.fetchone()[0]
        
        # Get channel count
        cursor.execute("""
            SELECT COUNT(*) FROM mining_channels WHERE guild_id = %s
        """, (guild_id,))
        channel_count = cursor.fetchone()[0]
        
        embed = discord.Embed(
            title="📊 Current Test Data Status",
            description=f"Test data overview for guild {guild_id}",
            color=0x3498db,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📈 Summary",
            value=f"• **{len(events)}** mining events\n"
                  f"• **{participant_count}** participation records\n"
                  f"• **{channel_count}** mining channels",
            inline=False
        )
        
        if events:
            event_list = []
            for event_id, date, participants, payout, is_open, payroll, pdf in events:
                status = []
                if is_open:
                    status.append("🟢 OPEN")
                if payroll:
                    status.append("💰 PAYROLL")
                if pdf:
                    status.append("📄 PDF")
                status_str = " ".join(status) if status else "⚪ CREATED"
                
                payout_str = f"{payout:,.0f} aUEC" if payout else "No payout"
                event_list.append(f"**{date}**: {participants} miners | {payout_str} | {status_str}")
            
            embed.add_field(
                name="📅 Recent Events",
                value="\n".join(event_list[:5]),
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        raise e

async def _cleanup_test_data(interaction, cursor, conn, guild_id):
    """Clean up all test data."""
    try:
        # Delete participants
        cursor.execute("""
            DELETE FROM mining_participation 
            WHERE event_id IN (SELECT id FROM events WHERE guild_id = %s)
        """, (guild_id,))
        deleted_participants = cursor.rowcount
        
        # Delete events
        cursor.execute("DELETE FROM events WHERE guild_id = %s", (guild_id,))
        deleted_events = cursor.rowcount
        
        # Delete test channels (only the fake test channel IDs)
        test_channel_ids = [111111111111111111, 222222222222222222, 333333333333333333, 444444444444444444]
        cursor.execute("""
            DELETE FROM mining_channels 
            WHERE guild_id = %s AND channel_id = ANY(%s)
        """, (guild_id, test_channel_ids))
        deleted_channels = cursor.rowcount
        
        conn.commit()
        
        embed = discord.Embed(
            title="🧹 Test Data Cleanup Complete",
            description="All test data has been removed from the database",
            color=0xff6b35,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🗑️ Deleted Data",
            value=f"• **{deleted_events}** mining events\n"
                  f"• **{deleted_participants}** participation records\n"
                  f"• **{deleted_channels}** test channels",
            inline=False
        )
        
        embed.add_field(
            name="✅ Database Clean",
            value="The database is now clean and ready for:\n"
                  "• Production use\n"
                  "• Fresh test data creation\n"
                  "• Real mining sessions",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        conn.rollback()
        raise e

    print("✅ Admin commands registered")
