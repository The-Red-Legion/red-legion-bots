"""
Admin Commands for Red Legion Bot

Administrative commands for managing events, users, and bot operations.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List, Dict
import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import get_cursor


class AdminCommands(commands.GroupCog, name="admin", description="Administrative commands (Admin only)"):
    """Administrative commands group."""
    
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
    
    @app_commands.command(name="delete-event", description="Delete a specific event and associated data")
    @app_commands.default_permissions(administrator=True)
    async def delete_event(self, interaction: discord.Interaction):
        """Delete a specific event with confirmation UI."""
        try:
            # Check admin permissions
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "❌ This command requires administrator permissions.",
                    ephemeral=True
                )
                return
            
            # Get available events
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT event_id, event_name, event_type, organizer_name, 
                           started_at, ended_at, status,
                           (SELECT COUNT(*) FROM participation WHERE event_id = events.event_id) as participant_count,
                           (SELECT COUNT(*) FROM payrolls WHERE event_id = events.event_id) as payroll_count
                    FROM events 
                    WHERE guild_id = %s
                    ORDER BY created_at DESC 
                    LIMIT 25
                """, (str(interaction.guild_id),))
                
                events = [dict(row) for row in cursor.fetchall()]
            
            if not events:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="ℹ️ No Events Found",
                        description="No events found in this server to delete.",
                        color=discord.Color.blue()
                    ),
                    ephemeral=True
                )
                return
            
            # Show event selection modal
            view = EventDeleteView(events)
            
            embed = discord.Embed(
                title="🗑️ Delete Events",
                description="⚠️ **WARNING: This action cannot be undone!**\n\n"
                           "Select one or more events to delete from the dropdown below.\n"
                           "This will permanently remove:\n"
                           "• The event records\n"
                           "• All participation data\n" 
                           "• Any payroll calculations\n"
                           "• All associated data",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="📊 Available Events",
                value=f"Found {len(events)} events in this server",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Error Loading Events",
                    description=f"An error occurred while loading events: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )


class EventDeleteView(discord.ui.View):
    """View for event deletion with dropdown and confirmation."""
    
    def __init__(self, events: List[Dict]):
        super().__init__(timeout=300)
        self.events = events
        
        # Add event selection dropdown
        self.add_item(EventDeleteDropdown(events))


class EventDeleteDropdown(discord.ui.Select):
    """Dropdown for selecting an event to delete."""
    
    def __init__(self, events: List[Dict]):
        self.events = events
        
        # Create options for dropdown
        options = []
        for event in events[:25]:  # Discord limit
            # Format event display
            status_emoji = {
                'active': '🟢',
                'closed': '🔴', 
                'cancelled': '⚫'
            }.get(event.get('status', 'unknown'), '❓')
            
            # Format date
            start_date = "Unknown"
            if event.get('started_at'):
                try:
                    if isinstance(event['started_at'], str):
                        from datetime import datetime
                        started_at = datetime.fromisoformat(event['started_at'].replace('Z', '+00:00'))
                    else:
                        started_at = event['started_at']
                    start_date = started_at.strftime("%m/%d %H:%M")
                except:
                    start_date = "Unknown"
            
            # Create option
            option_label = f"{status_emoji} {event['event_id']} - {event.get('event_name', 'Unnamed Event')}"
            option_description = f"{event.get('event_type', 'unknown').title()} • {start_date} • {event.get('participant_count', 0)} participants"
            
            options.append(discord.SelectOption(
                label=option_label[:100],  # Discord limit
                description=option_description[:100],  # Discord limit
                value=event['event_id'],
                emoji=status_emoji
            ))
        
        super().__init__(
            placeholder="Select one or more events to delete...",
            options=options,
            min_values=1,
            max_values=min(len(options), 25)  # Allow selecting up to all available events
        )
    
    async def callback(self, interaction: discord.Interaction):
        selected_event_ids = self.values  # Now handling multiple selections
        
        # Find the selected events
        selected_events = []
        for event in self.events:
            if event['event_id'] in selected_event_ids:
                selected_events.append(event)
        
        if not selected_events:
            await interaction.response.send_message(
                "❌ Selected events not found.",
                ephemeral=True
            )
            return
        
        # Show confirmation modal for bulk deletion
        modal = EventBulkDeleteConfirmationModal(selected_events)
        await interaction.response.send_modal(modal)


class EventDeleteConfirmationModal(discord.ui.Modal):
    """Modal for confirming event deletion."""
    
    def __init__(self, event: Dict):
        super().__init__(title=f'Confirm Delete: {event["event_id"]}')
        self.event = event
        
        # Confirmation input
        self.confirmation = discord.ui.TextInput(
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
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Delete event and all associated data
            with get_cursor() as cursor:
                cursor.execute("BEGIN")
                
                try:
                    # Delete in order to respect foreign key constraints
                    
                    # Delete payrolls first
                    cursor.execute("DELETE FROM payrolls WHERE event_id = %s", (self.event['event_id'],))
                    payroll_count = cursor.rowcount
                    
                    # Delete participation records
                    cursor.execute("DELETE FROM participation WHERE event_id = %s", (self.event['event_id'],))
                    participation_count = cursor.rowcount
                    
                    # Delete the event itself
                    cursor.execute("DELETE FROM events WHERE event_id = %s", (self.event['event_id'],))
                    event_deleted = cursor.rowcount > 0
                    
                    cursor.execute("COMMIT")
                    
                    if event_deleted:
                        embed = discord.Embed(
                            title="✅ Event Deleted Successfully",
                            description=f"Event **{self.event['event_id']}** has been permanently deleted.",
                            color=discord.Color.green()
                        )
                        
                        embed.add_field(
                            name="🗑️ Deleted Data",
                            value=f"• 1 event record\n"
                                  f"• {participation_count} participation records\n"
                                  f"• {payroll_count} payroll records",
                            inline=False
                        )
                        
                        embed.add_field(
                            name="📋 Event Details",
                            value=f"**Name:** {self.event.get('event_name', 'Unnamed')}\n"
                                  f"**Type:** {self.event.get('event_type', 'unknown').title()}\n"
                                  f"**Organizer:** {self.event.get('organizer_name', 'Unknown')}\n"
                                  f"**Status:** {self.event.get('status', 'unknown').title()}",
                            inline=False
                        )
                    else:
                        embed = discord.Embed(
                            title="⚠️ Event Not Found",
                            description=f"Event **{self.event['event_id']}** was not found or already deleted.",
                            color=discord.Color.orange()
                        )
                    
                except Exception as e:
                    cursor.execute("ROLLBACK")
                    raise e
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error Deleting Event",
                description=f"An error occurred while deleting the event: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


class EventBulkDeleteConfirmationModal(discord.ui.Modal):
    """Modal for confirming bulk event deletion."""
    
    def __init__(self, events: List[Dict]):
        event_count = len(events)
        super().__init__(title=f'Confirm Delete {event_count} Event{"s" if event_count > 1 else ""}')
        self.events = events
        
        # Show summary of what will be deleted
        event_ids = [event['event_id'] for event in events[:5]]  # Show first 5 IDs
        if len(events) > 5:
            event_ids.append(f"... and {len(events) - 5} more")
        
        # Confirmation input - require typing the count
        self.confirmation = discord.ui.TextInput(
            label=f'Type "{event_count}" to confirm deletion of {event_count} events',
            placeholder=f'Type {event_count} to confirm bulk deletion',
            required=True,
            max_length=10
        )
        self.add_item(self.confirmation)
        
        # Event list display
        self.event_summary = discord.ui.TextInput(
            label='Events to be deleted (READ ONLY)',
            default=", ".join(event_ids),
            required=False,
            max_length=1000,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.event_summary)
    
    async def on_submit(self, interaction: discord.Interaction):
        expected_count = str(len(self.events))
        if self.confirmation.value.strip() != expected_count:
            await interaction.response.send_message(
                f"❌ Deletion cancelled. You must type '{expected_count}' to confirm deletion of {len(self.events)} events.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            deleted_events = []
            total_participation_deleted = 0
            total_payrolls_deleted = 0
            
            # Delete events in bulk transaction
            with get_cursor() as cursor:
                cursor.execute("BEGIN")
                
                try:
                    for event in self.events:
                        event_id = event['event_id']
                        
                        # Delete payrolls for this event
                        cursor.execute("DELETE FROM payrolls WHERE event_id = %s", (event_id,))
                        total_payrolls_deleted += cursor.rowcount
                        
                        # Delete participation records for this event
                        cursor.execute("DELETE FROM participation WHERE event_id = %s", (event_id,))
                        total_participation_deleted += cursor.rowcount
                        
                        # Delete the event itself
                        cursor.execute("DELETE FROM events WHERE event_id = %s", (event_id,))
                        if cursor.rowcount > 0:
                            deleted_events.append(event_id)
                    
                    cursor.execute("COMMIT")
                    
                    # Create success embed
                    embed = discord.Embed(
                        title="✅ Bulk Event Deletion Successful",
                        description=f"Successfully deleted **{len(deleted_events)}** events.",
                        color=discord.Color.green()
                    )
                    
                    embed.add_field(
                        name="🗑️ Deleted Data Summary",
                        value=f"• {len(deleted_events)} event records\n"
                              f"• {total_participation_deleted} participation records\n" 
                              f"• {total_payrolls_deleted} payroll calculations",
                        inline=False
                    )
                    
                    if len(deleted_events) <= 10:
                        embed.add_field(
                            name="📋 Deleted Events",
                            value=", ".join(deleted_events),
                            inline=False
                        )
                    else:
                        embed.add_field(
                            name="📋 Deleted Events (First 10)",
                            value=", ".join(deleted_events[:10]) + f"\n... and {len(deleted_events) - 10} more",
                            inline=False
                        )
                    
                    embed.set_footer(text="⚠️ This action cannot be undone")
                    
                except Exception as e:
                    cursor.execute("ROLLBACK")
                    raise e
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error During Bulk Deletion",
                description=f"An error occurred while deleting events: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


    @app_commands.command(name="voice-diagnostic", description="Diagnose voice channel connectivity issues")
    @app_commands.default_permissions(administrator=True)
    async def voice_diagnostic(self, interaction: discord.Interaction):
        """Comprehensive voice channel diagnostic test."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            guild = interaction.guild
            bot_member = guild.get_member(self.bot.user.id)
            
            # Create diagnostic embed
            embed = discord.Embed(
                title="🔧 Voice Channel Diagnostic Report",
                description="Testing bot voice capabilities and channel configurations",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            # 1. Bot Permissions Check
            permissions_info = []
            guild_perms = bot_member.guild_permissions
            permissions_info.append(f"Connect: {'✅' if guild_perms.connect else '❌'}")
            permissions_info.append(f"Speak: {'✅' if guild_perms.speak else '❌'}")
            permissions_info.append(f"Use Voice Activity: {'✅' if guild_perms.use_voice_activation else '❌'}")
            permissions_info.append(f"View Channels: {'✅' if guild_perms.view_channel else '❌'}")
            permissions_info.append(f"Administrator: {'✅' if guild_perms.administrator else '❌'}")
            
            embed.add_field(
                name="🛡️ Bot Guild Permissions",
                value="\n".join(permissions_info),
                inline=True
            )
            
            # 2. Check Mining Channels Configuration
            try:
                from config.settings import get_sunday_mining_channels, SUNDAY_MINING_CHANNELS_FALLBACK
                
                # Try database lookup with fallback if it hangs/fails
                try:
                    channels_config = get_sunday_mining_channels(guild.id)
                except Exception as db_error:
                    print(f"Database lookup failed, using fallback: {db_error}")
                    channels_config = SUNDAY_MINING_CHANNELS_FALLBACK
                
                channel_status = []
                dispatch_channel = None
                voice_channels = []
                
                if channels_config:
                    # Check dispatch channel
                    if 'dispatch' in channels_config:
                        dispatch_id = int(channels_config['dispatch'])
                        dispatch_channel = guild.get_channel(dispatch_id)
                        if dispatch_channel:
                            channel_status.append(f"📢 Dispatch: `{dispatch_channel.name}` ✅")
                        else:
                            channel_status.append(f"📢 Dispatch: ID `{dispatch_id}` ❌ Not Found")
                    
                    # Check voice channels (all non-dispatch channels)
                    voice_channel_configs = {k: v for k, v in channels_config.items() if k != 'dispatch'}
                    for channel_name, vc_id_str in voice_channel_configs.items():
                        try:
                            vc_id = int(vc_id_str)
                            vc = guild.get_channel(vc_id)
                            if vc:
                                # Check bot permissions in this specific channel
                                vc_perms = vc.permissions_for(bot_member)
                                perm_status = "✅" if (vc_perms.connect and vc_perms.view_channel) else "❌"
                                channel_status.append(f"🎤 Voice: `{vc.name}` {perm_status}")
                                voice_channels.append((vc, vc_perms))
                            else:
                                channel_status.append(f"🎤 Voice: ID `{vc_id}` ❌ Not Found")
                        except (ValueError, TypeError):
                            channel_status.append(f"🎤 Voice: `{channel_name}` ❌ Invalid ID")
                else:
                    channel_status.append("❌ No mining channels configured")
                
                embed.add_field(
                    name="📋 Channel Configuration",
                    value="\n".join(channel_status) if channel_status else "No channels found",
                    inline=True
                )
                
                # 3. Test Voice Connection
                connection_tests = []
                
                if voice_channels:
                    for vc, perms in voice_channels[:2]:  # Test first 2 channels
                        try:
                            # Check if we can theoretically connect
                            if perms.connect and perms.view_channel:
                                # Try to get voice client info
                                if vc.guild.voice_client:
                                    if vc.guild.voice_client.channel == vc:
                                        connection_tests.append(f"🟢 `{vc.name}`: Already connected")
                                    else:
                                        connection_tests.append(f"🟡 `{vc.name}`: Connected elsewhere")
                                else:
                                    connection_tests.append(f"🔵 `{vc.name}`: Ready to connect")
                                    
                                # Check user limit
                                if vc.user_limit > 0:
                                    current_users = len(vc.members)
                                    if current_users >= vc.user_limit:
                                        connection_tests.append(f"⚠️ `{vc.name}`: Channel full ({current_users}/{vc.user_limit})")
                                    else:
                                        connection_tests.append(f"👥 `{vc.name}`: Space available ({current_users}/{vc.user_limit})")
                                else:
                                    connection_tests.append(f"👥 `{vc.name}`: No user limit")
                            else:
                                missing_perms = []
                                if not perms.connect: missing_perms.append("Connect")
                                if not perms.view_channel: missing_perms.append("View")
                                connection_tests.append(f"❌ `{vc.name}`: Missing {', '.join(missing_perms)}")
                                
                        except Exception as e:
                            connection_tests.append(f"💥 `{vc.name}`: Error - {str(e)[:50]}")
                
                embed.add_field(
                    name="🔗 Voice Connection Tests",
                    value="\n".join(connection_tests) if connection_tests else "No voice channels to test",
                    inline=False
                )
                
                # 4. Current Voice State
                voice_state_info = []
                voice_client = guild.voice_client
                
                if voice_client:
                    voice_state_info.append(f"Connected: ✅ `{voice_client.channel.name}`")
                    voice_state_info.append(f"Latency: {voice_client.latency:.2f}ms")
                    voice_state_info.append(f"Is Connected: {'✅' if voice_client.is_connected() else '❌'}")
                else:
                    voice_state_info.append("Connected: ❌ Not in any channel")
                
                embed.add_field(
                    name="🎵 Current Voice State",
                    value="\n".join(voice_state_info),
                    inline=True
                )
                
                # 5. Recommendations
                recommendations = []
                
                if not guild_perms.connect:
                    recommendations.append("🔧 Grant bot 'Connect' permission")
                if not guild_perms.view_channel:
                    recommendations.append("🔧 Grant bot 'View Channels' permission")
                if not channels_config:
                    recommendations.append("🔧 Configure mining channels in settings")
                if dispatch_channel is None and channels_config and 'dispatch_channel_id' in channels_config:
                    recommendations.append("🔧 Fix dispatch channel configuration")
                
                for vc, perms in voice_channels:
                    if not perms.connect:
                        recommendations.append(f"🔧 Grant connect permission in `{vc.name}`")
                
                if not recommendations:
                    recommendations.append("✅ All configurations look good!")
                
                embed.add_field(
                    name="💡 Recommendations",
                    value="\n".join(recommendations[:5]),  # Limit to 5 recommendations
                    inline=False
                )
                
                # Add footer with debug info
                embed.set_footer(text=f"Guild ID: {guild.id} | Bot ID: {self.bot.user.id}")
                
            except Exception as config_error:
                embed.add_field(
                    name="❌ Configuration Error",
                    value=f"Could not load channel config: {str(config_error)}",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Diagnostic failed: {str(e)}",
                ephemeral=True
            )


async def setup(bot):
    """Setup function for discord.py extension loading."""
    await bot.add_cog(AdminCommands(bot))