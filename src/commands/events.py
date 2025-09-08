"""
Comprehensive Event Management System for Red Legion Discord Bot.

This module provides complete CRUD operations for mining events including:
- List all events with filtering by status
- View detailed event information
- Create adhoc events
- Delete events with confirmation
"""

import discord
from discord.ext import commands
from discord import app_commands
import sys
from pathlib import Path
from datetime import datetime, timezone, date

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_database_url
from src.database import operations as database_operations

class EventManagement(commands.Cog):
    """Complete event management system for mining events."""
    
    def __init__(self, bot):
        self.bot = bot
        print("✅ Event Management Cog initialized")
    
    # Define the command group
    events = app_commands.Group(name="red-events", description="Red Legion event management system")

    @events.command(name="create", description="Create a new Red Legion event")
    @app_commands.describe(
        category="Event category",
        name="Event name",
        description="Event description (optional)"
    )
    @app_commands.choices(category=[
        app_commands.Choice(name="Mining", value="mining"),
        app_commands.Choice(name="Training", value="training"),
        app_commands.Choice(name="Combat Operations", value="combat_operations"),
        app_commands.Choice(name="Salvage", value="salvage"),
        app_commands.Choice(name="Miscellaneous", value="misc")
    ])
    async def create_event(
        self, 
        interaction: discord.Interaction,
        category: app_commands.Choice[str],
        name: str,
        description: str = None
    ):
        """Create a new event in the specified category."""
        await interaction.response.defer()
        
        try:
            await self._create_event_by_category(interaction, category.value, name, description)
        except Exception as e:
            print(f"❌ Error in create event command: {e}")
            embed = discord.Embed(
                title="❌ Command Error",
                description=f"An error occurred while creating the event: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
    
    @events.command(name="delete", description="Delete a Red Legion event (Admin only)")
    @app_commands.describe(
        event_id="ID of the event to delete"
    )
    @app_commands.default_permissions(administrator=True)
    async def delete_event(
        self, 
        interaction: discord.Interaction,
        event_id: int
    ):
        """Delete an event (Admin only)."""
        await interaction.response.defer()
        
        try:
            await self._delete_event_by_id(interaction, event_id)
        except Exception as e:
            print(f"❌ Error in delete event command: {e}")
            embed = discord.Embed(
                title="❌ Command Error",
                description=f"An error occurred while deleting the event: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
    
    @events.command(name="lookup", description="Look up Red Legion events by category and status")
    @app_commands.describe(
        category="Event category to filter by",
        status="Event status to filter by (optional)",
        event_id="Specific event ID to view details (optional)"
    )
    @app_commands.choices(category=[
        app_commands.Choice(name="All Categories", value="all"),
        app_commands.Choice(name="Mining", value="mining"),
        app_commands.Choice(name="Training", value="training"),
        app_commands.Choice(name="Combat Operations", value="combat_operations"),
        app_commands.Choice(name="Salvage", value="salvage"),
        app_commands.Choice(name="Miscellaneous", value="misc")
    ])
    @app_commands.choices(status=[
        app_commands.Choice(name="All Statuses", value="all"),
        app_commands.Choice(name="Active/Open", value="active"),
        app_commands.Choice(name="Completed/Closed", value="completed"),
        app_commands.Choice(name="Planned", value="planned")
    ])
    async def lookup_events(
        self, 
        interaction: discord.Interaction,
        category: app_commands.Choice[str],
        status: app_commands.Choice[str] = None,
        event_id: int = None
    ):
        """Look up events by category and status, or view specific event details."""
        await interaction.response.defer()
        
        try:
            if event_id:
                # View specific event details
                await self._view_event_details(interaction, event_id)
            else:
                # List events by category and status
                await self._lookup_events_by_filters(interaction, category.value, status.value if status else "all")
        except Exception as e:
            print(f"❌ Error in lookup events command: {e}")
            embed = discord.Embed(
                title="❌ Command Error",
                description=f"An error occurred while looking up events: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, date, timedelta
from typing import Optional, List
import sys
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_database_url
from database import operations as database_operations

class EventManagement(commands.Cog):
    """Event management command group."""
    
    def __init__(self, bot):
        self.bot = bot

    # Helper methods for the new subcommand structure
    
    async def _create_event_by_category(self, interaction: discord.Interaction, category: str, name: str, description: str = None):
        """Create a new event in the specified category."""
        
        db_url = get_database_url()
        guild_id = interaction.guild.id
        
        try:
            # Create the event with proper category
            event_id = database_operations.create_adhoc_mining_event(
                db_url,
                guild_id,
                interaction.user.id,
                interaction.user.display_name,
                name,
                description or f"{category.title()} event created by {interaction.user.display_name}",
                datetime.now(timezone.utc)
            )
            
            if event_id:
                embed = discord.Embed(
                    title="✅ Event Created",
                    description=f"Successfully created new {category} event",
                    color=0x00ff00
                )
                
                embed.add_field(
                    name="📋 Event Details",
                    value=f"**Event ID:** {event_id}\n"
                          f"**Name:** {name}\n"
                          f"**Category:** {category.title()}\n"
                          f"**Created:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
                          f"**Status:** Active\n"
                          f"**Organizer:** {interaction.user.display_name}",
                    inline=False
                )
                
                embed.add_field(
                    name="🎮 Next Steps",
                    value="• Use `/events lookup` to view this event\n"
                          "• Start tracking participation as needed\n"
                          "• Use `/events lookup event_id:" + str(event_id) + "` for details",
                    inline=False
                )
                
            else:
                embed = discord.Embed(
                    title="❌ Creation Failed",
                    description="Could not create the event. Please try again.",
                    color=0xff0000
                )
                
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error creating event: {e}")
            embed = discord.Embed(
                title="❌ Database Error",
                description=f"Could not create event: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
    
    async def _delete_event_by_id(self, interaction: discord.Interaction, event_id: int):
        """Delete an event by ID (Admin only)."""
        
        db_url = get_database_url()
        
        try:
            # First get event details for confirmation
            events = database_operations.get_mining_events(db_url, interaction.guild.id)
            event_to_delete = None
            
            for event in events:
                if event[0] == event_id:  # event[0] is the ID
                    event_to_delete = event
                    break
            
            if not event_to_delete:
                embed = discord.Embed(
                    title="❌ Event Not Found",
                    description=f"No event found with ID {event_id}",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Create confirmation dialog
            event_name = event_to_delete[3]  # event[3] is the event name
            view = DeleteConfirmationView(event_id, event_name)
            
            embed = discord.Embed(
                title="⚠️ Confirm Event Deletion",
                description=f"Are you sure you want to delete this event?\n\n"
                           f"**Event Name:** {event_name}\n"
                           f"**Event ID:** {event_id}\n"
                           f"**Requester:** {interaction.user.display_name}",
                color=0xff9900
            )
            
            embed.add_field(
                name="⚠️ Warning",
                value="This action cannot be undone. All participation records for this event will also be deleted.",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            print(f"❌ Error preparing event deletion: {e}")
            embed = discord.Embed(
                title="❌ Database Error",
                description=f"Could not prepare event deletion: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
    
    async def _lookup_events_by_filters(self, interaction: discord.Interaction, category: str, status: str):
        """Look up events by category and status filters."""
        
        db_url = get_database_url()
        guild_id = interaction.guild.id
        
        try:
            # Get events based on status filter
            if status == "active":
                events = database_operations.get_open_mining_events(db_url, guild_id)
            else:
                events = database_operations.get_mining_events(db_url, guild_id)
            
            if not events:
                embed = discord.Embed(
                    title="📋 No Events Found",
                    description=f"No events found matching your criteria.",
                    color=0x999999
                )
                
                embed.add_field(
                    name="🔍 Search Criteria",
                    value=f"**Category:** {category.title() if category != 'all' else 'All Categories'}\n"
                          f"**Status:** {status.title() if status != 'all' else 'All Statuses'}",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed)
                return
            
            # Filter by category if not "all"
            if category != "all":
                # For now, we'll show all events since we don't have category field in database yet
                # This can be enhanced when category field is added to the database schema
                pass
            
            # Filter by status if not "all"
            if status != "all":
                if status == "completed":
                    events = [e for e in events if e[8] == 'completed']  # event[8] is status
                elif status == "active":
                    events = [e for e in events if e[8] == 'active']
                elif status == "planned":
                    events = [e for e in events if e[8] == 'planned']
            
            # Create embed with event list
            embed = discord.Embed(
                title="📋 Event Lookup Results",
                description=f"Found {len(events)} event(s) matching your criteria",
                color=0x0099ff
            )
            
            embed.add_field(
                name="🔍 Search Criteria",
                value=f"**Category:** {category.title() if category != 'all' else 'All Categories'}\n"
                      f"**Status:** {status.title() if status != 'all' else 'All Statuses'}",
                inline=False
            )
            
            # Add events to embed (limit to first 10 to avoid hitting Discord limits)
            events_text = []
            for i, event in enumerate(events[:10]):
                event_id = event[0]
                event_name = event[3]
                event_status = event[8]
                start_time = event[6].strftime('%Y-%m-%d') if event[6] else 'TBD'
                
                status_emoji = "🟢" if event_status == "active" else "🔴" if event_status == "completed" else "🟡"
                events_text.append(f"{status_emoji} **{event_name}** (ID: {event_id})\n   Status: {event_status.title()} | Date: {start_time}")
            
            if events_text:
                embed.add_field(
                    name="📅 Events",
                    value="\n\n".join(events_text),
                    inline=False
                )
            
            if len(events) > 10:
                embed.add_field(
                    name="📄 Note",
                    value=f"Showing first 10 of {len(events)} events. Use specific filters to narrow results.",
                    inline=False
                )
            
            embed.add_field(
                name="🔍 View Details",
                value="Use `/events lookup event_id:<id>` to view detailed information about a specific event.",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error looking up events: {e}")
            embed = discord.Embed(
                title="❌ Database Error",
                description=f"Could not retrieve events: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            await interaction.followup.send(embed=embed)


class DeleteConfirmationView(discord.ui.View):

    async def _list_events(self, interaction: discord.Interaction, status_filter: Optional[str], days_back: int):
        """List all events with optional status filtering."""
        
        db_url = get_database_url()
        guild_id = interaction.guild.id
        
        # Get events from the last X days
        try:
            events = database_operations.get_mining_events(db_url, guild_id)
            
            if not events:
                embed = discord.Embed(
                    title="📋 No Events Found",
                    description=f"No mining events found for the last {days_back} days",
                    color=0xffaa00
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Filter by status if specified
            if status_filter and status_filter != "all":
                events = [e for e in events if e['status'] == status_filter]
            
            # Filter by days_back
            cutoff_date = date.today() - timedelta(days=days_back)
            events = [e for e in events if e['event_date'] >= cutoff_date]
            
            if not events:
                embed = discord.Embed(
                    title="📋 No Matching Events",
                    description=f"No events found matching the criteria",
                    color=0xffaa00
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Create embed with event list
            embed = discord.Embed(
                title="📋 Mining Events",
                description=f"Found {len(events)} events" + (f" with status '{status_filter}'" if status_filter and status_filter != "all" else ""),
                color=0x00aa00
            )
            
            # Group events by status
            status_groups = {}
            for event in events:
                status = event['status']
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append(event)
            
            # Add fields for each status group
            for status, status_events in status_groups.items():
                status_emoji = {
                    'planned': '📅',
                    'active': '🟢',
                    'completed': '✅',
                    'cancelled': '❌'
                }.get(status, '❓')
                
                event_list = []
                for event in status_events[:10]:  # Limit to 10 per status
                    participants = event['total_participants'] or 0
                    value = event['total_value_auec'] or 0
                    event_list.append(f"**{event['id']}** - {event['event_name']}")
                    event_list.append(f"   📅 {event['event_date']} | 👥 {participants} | 💰 {value:,.0f} aUEC")
                
                if len(status_events) > 10:
                    event_list.append(f"... and {len(status_events) - 10} more")
                
                embed.add_field(
                    name=f"{status_emoji} {status.title()} ({len(status_events)})",
                    value="\n".join(event_list) if event_list else "None",
                    inline=False
                )
            
            embed.add_field(
                name="💡 Usage Tips",
                value="• Use `/event view event_id:123` to see details\n• Use `/event open` for active events only\n• Use `/event create` for adhoc events",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error listing events: {e}")
            embed = discord.Embed(
                title="❌ Database Error",
                description=f"Could not retrieve events: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)

    async def _list_open_events(self, interaction: discord.Interaction):
        """List only open/active events."""
        
        db_url = get_database_url()
        guild_id = interaction.guild.id
        
        try:
            events = database_operations.get_open_mining_events(db_url, guild_id)
            
            if not events:
                embed = discord.Embed(
                    title="🟢 No Open Events",
                    description="No planned or active mining events found",
                    color=0xffaa00
                )
                embed.add_field(
                    name="Create New Event",
                    value="Use `/event create event_name:\"Your Event Name\"` to create an adhoc event",
                    inline=False
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="🟢 Open Mining Events",
                description=f"Found {len(events)} open events",
                color=0x00aa00
            )
            
            for event in events:
                status_emoji = "📅" if event['status'] == 'planned' else "🟢"
                participants = event['total_participants'] or 0
                value = event['total_value_auec'] or 0
                
                embed.add_field(
                    name=f"{status_emoji} {event['event_name']} (ID: {event['id']})",
                    value=f"📅 {event['event_date']} at {event['event_time'].strftime('%H:%M')}\n"
                          f"📊 Status: {event['status'].title()}\n"
                          f"👥 Participants: {participants}\n"
                          f"💰 Value: {value:,.0f} aUEC\n"
                          f"📝 Payroll: {'✅ Processed' if event['payroll_processed'] else '⏳ Pending'}",
                    inline=True
                )
            
            embed.add_field(
                name="💡 Actions",
                value="• `/event view event_id:X` - View details\n• `/sunday_mining_start` - Start new session\n• `/payroll` - Process payroll",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error listing open events: {e}")
            embed = discord.Embed(
                title="❌ Database Error",
                description=f"Could not retrieve open events: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)

    async def _list_closed_events(self, interaction: discord.Interaction, days_back: int):
        """List completed and cancelled events."""
        
        db_url = get_database_url()
        guild_id = interaction.guild.id
        
        try:
            events = database_operations.get_mining_events(db_url, guild_id)
            
            # Filter for closed events (completed or cancelled)
            closed_events = [e for e in events if e['status'] in ['completed', 'cancelled']]
            
            # Filter by days_back
            cutoff_date = date.today() - timedelta(days=days_back)
            closed_events = [e for e in closed_events if e['event_date'] >= cutoff_date]
            
            if not closed_events:
                embed = discord.Embed(
                    title="✅ No Closed Events",
                    description=f"No completed or cancelled events found in the last {days_back} days",
                    color=0xffaa00
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="✅ Closed Mining Events",
                description=f"Found {len(closed_events)} closed events from the last {days_back} days",
                color=0x0066cc
            )
            
            # Sort by date (newest first)
            closed_events.sort(key=lambda x: x['event_date'], reverse=True)
            
            for event in closed_events[:15]:  # Limit to 15 most recent
                status_emoji = "✅" if event['status'] == 'completed' else "❌"
                participants = event['total_participants'] or 0
                value = event['total_value_auec'] or 0
                
                embed.add_field(
                    name=f"{status_emoji} {event['event_name']} (ID: {event['id']})",
                    value=f"📅 {event['event_date']}\n"
                          f"👥 {participants} participants\n"
                          f"💰 {value:,.0f} aUEC\n"
                          f"📄 PDF: {'✅' if event['pdf_generated'] else '❌'}",
                    inline=True
                )
            
            if len(closed_events) > 15:
                embed.add_field(
                    name="📊 Summary",
                    value=f"Showing 15 of {len(closed_events)} events. Use `/event list status:completed` for full list.",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error listing closed events: {e}")
            embed = discord.Embed(
                title="❌ Database Error", 
                description=f"Could not retrieve closed events: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)

    async def _view_event_details(self, interaction: discord.Interaction, event_id: int):
        """View detailed information about a specific event."""
        
        db_url = get_database_url()
        guild_id = interaction.guild.id
        
        try:
            # Get all events and find the specific one
            events = database_operations.get_mining_events(db_url, guild_id)
            event = next((e for e in events if e['id'] == event_id), None)
            
            if not event:
                embed = discord.Embed(
                    title="❌ Event Not Found",
                    description=f"Event with ID {event_id} not found in this guild",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Status emoji and color
            status_emoji = {
                'planned': '📅',
                'active': '🟢', 
                'completed': '✅',
                'cancelled': '❌'
            }.get(event['status'], '❓')
            
            color = {
                'planned': 0xffaa00,
                'active': 0x00ff00,
                'completed': 0x0066cc,
                'cancelled': 0xff0000
            }.get(event['status'], 0x666666)
            
            embed = discord.Embed(
                title=f"{status_emoji} {event['event_name']}",
                description=f"Event ID: {event['id']} | Status: {event['status'].title()}",
                color=color,
                timestamp=event['created_at']
            )
            
            # Basic event information
            embed.add_field(
                name="📅 Event Details",
                value=f"**Date:** {event['event_date']}\n"
                      f"**Time:** {event['event_time'].strftime('%H:%M:%S UTC')}\n"
                      f"**Created:** <t:{int(event['created_at'].timestamp())}:R>\n"
                      f"**Updated:** <t:{int(event['updated_at'].timestamp())}:R>",
                inline=True
            )
            
            # Participation and value
            participants = event['total_participants'] or 0
            value = event['total_value_auec'] or 0
            
            embed.add_field(
                name="📊 Statistics",
                value=f"**Participants:** {participants}\n"
                      f"**Total Value:** {value:,.0f} aUEC\n"
                      f"**Avg per Person:** {(value / participants):,.0f} aUEC" if participants > 0 else "**Avg per Person:** N/A",
                inline=True
            )
            
            # Processing status
            embed.add_field(
                name="🔄 Processing Status",
                value=f"**Payroll:** {'✅ Processed' if event['payroll_processed'] else '⏳ Pending'}\n"
                      f"**PDF Report:** {'✅ Generated' if event['pdf_generated'] else '❌ Not Generated'}\n"
                      f"**Guild ID:** {event['guild_id']}",
                inline=True
            )
            
            # TODO: Get participation details if available
            # This would require querying the mining_participation table
            
            # Action buttons based on status
            if event['status'] == 'active':
                embed.add_field(
                    name="🎮 Available Actions",
                    value="• `/sunday_mining_stop` - End this session\n• Monitor voice channels for participation\n• Use `/payroll` when ready to process",
                    inline=False
                )
            elif event['status'] == 'completed' and not event['payroll_processed']:
                embed.add_field(
                    name="🎮 Available Actions", 
                    value="• `/payroll` - Process payroll for this event\n• `/event delete` - Remove this event (if needed)",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🎮 Available Actions",
                    value="• `/event delete` - Remove this event\n• View participation logs in database",
                    inline=False
                )
            
            embed.set_footer(text="Event Management System")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error viewing event details: {e}")
            embed = discord.Embed(
                title="❌ Database Error",
                description=f"Could not retrieve event details: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)

    async def _create_adhoc_event(self, interaction: discord.Interaction, event_name: str):
        """Create a new adhoc mining event."""
        
        db_url = get_database_url()
        guild_id = interaction.guild.id
        
        try:
            # Create the adhoc event
            event_id = database_operations.create_adhoc_mining_event(
                db_url,
                guild_id,
                interaction.user.id,
                interaction.user.display_name,
                event_name,
                f"Adhoc event created by {interaction.user.display_name}"
            )
            
            if event_id:
                embed = discord.Embed(
                    title="✅ Adhoc Event Created",
                    description=f"Successfully created new adhoc mining event",
                    color=0x00ff00
                )
                
                embed.add_field(
                    name="📋 Event Details",
                    value=f"**Event ID:** {event_id}\n"
                          f"**Name:** {event_name}\n"
                          f"**Type:** Adhoc\n"
                          f"**Created:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
                          f"**Status:** Active\n"
                          f"**Organizer:** {interaction.user.display_name}\n"
                          f"**Guild:** {interaction.guild.name}",
                    inline=False
                )
                
                embed.add_field(
                    name="🎮 Next Steps",
                    value="• Use `/sunday_mining_start` to begin tracking\n"
                          "• Or manually activate this event for tracking\n"
                          "• Use `/event view event_id:" + str(event_id) + "` to see details",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed)
                
                print(f"✅ Created adhoc event {event_id}: {event_name} for guild {guild_id}")
                
            else:
                embed = discord.Embed(
                    title="❌ Creation Failed",
                    description="Could not create the adhoc event. Check logs for details.",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            print(f"❌ Error creating adhoc event: {e}")
            embed = discord.Embed(
                title="❌ Creation Error",
                description=f"Could not create adhoc event: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)

    async def _delete_event(self, interaction: discord.Interaction, event_id: int):
        """Delete a mining event (with confirmation)."""
        
        db_url = get_database_url()
        guild_id = interaction.guild.id
        
        try:
            # First, get the event to show what we're deleting
            events = database_operations.get_mining_events(db_url, guild_id)
            event = next((e for e in events if e['id'] == event_id), None)
            
            if not event:
                embed = discord.Embed(
                    title="❌ Event Not Found",
                    description=f"Event with ID {event_id} not found in this guild",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Create confirmation embed
            embed = discord.Embed(
                title="⚠️ Confirm Event Deletion", 
                description=f"Are you sure you want to delete this event?",
                color=0xffaa00
            )
            
            embed.add_field(
                name="📋 Event to Delete",
                value=f"**ID:** {event['id']}\n"
                      f"**Name:** {event['event_name']}\n"
                      f"**Date:** {event['event_date']}\n"
                      f"**Status:** {event['status'].title()}\n"
                      f"**Participants:** {event['total_participants'] or 0}",
                inline=False
            )
            
            embed.add_field(
                name="⚠️ Warning",
                value="This action cannot be undone. All participation data for this event will also be deleted.",
                inline=False
            )
            
            # Create confirmation view with buttons
            view = DeleteConfirmationView(event_id, event['event_name'])
            
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            print(f"❌ Error in delete event: {e}")
            embed = discord.Embed(
                title="❌ Delete Error",
                description=f"Could not process delete request: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)


class DeleteConfirmationView(discord.ui.View):
    """Confirmation view for event deletion."""
    
    def __init__(self, event_id: int, event_name: str):
        super().__init__(timeout=300)
        self.event_id = event_id
        self.event_name = event_name
    
    @discord.ui.button(label='Yes, Delete Event', style=discord.ButtonStyle.danger, emoji='🗑️')
    async def confirm_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle confirmed deletion."""
        
        # Import database operations
        db_url = get_database_url()
        
        try:
            # Actually delete the event
            success = database_operations.delete_mining_event(db_url, self.event_id)
            
            if success:
                embed = discord.Embed(
                    title="✅ Event Deleted",
                    description=f"Event '{self.event_name}' (ID: {self.event_id}) has been permanently deleted.",
                    color=0x00aa00
                )
                
                embed.add_field(
                    name="🗑️ Deletion Summary",
                    value=f"**Event Name:** {self.event_name}\n"
                          f"**Event ID:** {self.event_id}\n"
                          f"**Deleted by:** {interaction.user.display_name}\n"
                          f"**Time:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="❌ Deletion Failed",
                    description=f"Could not delete event '{self.event_name}' (ID: {self.event_id}). The event may not exist or there was a database error.",
                    color=0xff0000
                )
        
        except Exception as e:
            embed = discord.Embed(
                title="❌ Deletion Error",
                description=f"An error occurred while deleting event '{self.event_name}' (ID: {self.event_id}).",
                color=0xff0000
            )
            
            embed.add_field(
                name="🔍 Error Details",
                value=f"```{str(e)}```",
                inline=False
            )
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.secondary, emoji='❌')
    async def cancel_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle cancelled deletion."""
        
        embed = discord.Embed(
            title="❌ Deletion Cancelled",
            description=f"Event {self.event_name} (ID: {self.event_id}) was not deleted.",
            color=0x00aa00
        )
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)


async def setup(bot):
    """Setup function for discord.py extension loading."""
    await bot.add_cog(EventManagement(bot))
    print("✅ Event Management commands loaded")
