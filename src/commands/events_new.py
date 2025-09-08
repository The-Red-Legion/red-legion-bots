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
import importlib.util

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_database_url

# Import database operations using importlib to avoid conflicts with operations/ directory
operations_path = Path(__file__).parent.parent / "database" / "operations.py"
spec = importlib.util.spec_from_file_location("database_operations", operations_path)
database_operations = importlib.util.module_from_spec(spec)
spec.loader.exec_module(database_operations)

class EventManagement(commands.Cog):
    """Complete event management system for mining events."""
    
    def __init__(self, bot):
        self.bot = bot
        print("✅ Event Management Cog initialized")
    
    @app_commands.command(name="event", description="Comprehensive event management system")
    @app_commands.describe(
        action="What action to perform",
        event_id="Event ID for view/delete actions",
        filter_status="Filter events by status (for list action)",
        name="Name for new adhoc event",
        description="Description for new adhoc event"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="List All Events", value="list"),
        app_commands.Choice(name="Filter Open Events", value="open"),
        app_commands.Choice(name="Filter Closed Events", value="closed"),
        app_commands.Choice(name="View Event Details", value="view"),
        app_commands.Choice(name="Create Adhoc Event", value="create"),
        app_commands.Choice(name="Delete Event", value="delete")
    ])
    async def event_command(
        self, 
        interaction: discord.Interaction,
        action: app_commands.Choice[str],
        event_id: int = None,
        filter_status: str = None,
        name: str = None,
        description: str = None
    ):
        """Main event management command with multiple actions."""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, date, timedelta
from typing import Optional, List
import sys
import importlib.util
from pathlib import Path

# Import database operations from the correct file
operations_path = Path(__file__).parent.parent.parent / 'database' / 'operations.py'
spec = importlib.util.spec_from_file_location("database_operations", operations_path)
database_operations = importlib.util.module_from_spec(spec)
spec.loader.exec_module(database_operations)

from config.settings import get_database_url

class EventManagement(commands.Cog):
    """Event management command group."""
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="event", description="Event management - list, view, create, or delete events")
    @app_commands.describe(
        action="What you want to do with events",
        event_id="Event ID for view/delete actions",
        status="Filter events by status",
        event_name="Name for new adhoc event",
        days_back="How many days back to search (default: 30)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="List All Events", value="list"),
        app_commands.Choice(name="List Open Events", value="open"),
        app_commands.Choice(name="List Closed Events", value="closed"),
        app_commands.Choice(name="View Event Details", value="view"),
        app_commands.Choice(name="Create Adhoc Event", value="create"),
        app_commands.Choice(name="Delete Event", value="delete")
    ])
    @app_commands.choices(status=[
        app_commands.Choice(name="All", value="all"),
        app_commands.Choice(name="Planned", value="planned"),
        app_commands.Choice(name="Active", value="active"),
        app_commands.Choice(name="Completed", value="completed"),
        app_commands.Choice(name="Cancelled", value="cancelled")
    ])
    async def event_command(
        self, 
        interaction: discord.Interaction,
        action: str,
        event_id: Optional[int] = None,
        status: Optional[str] = None,
        event_name: Optional[str] = None,
        days_back: Optional[int] = 30
    ):
        """Main event management command."""
        
        await interaction.response.defer()
        
        db_url = get_database_url()
        if not db_url:
            embed = discord.Embed(
                title="❌ Database Error",
                description="Database connection not available",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            return

        try:
            if action == "list":
                await self._list_events(interaction, status, days_back)
            elif action == "open":
                await self._list_open_events(interaction)
            elif action == "closed":
                await self._list_closed_events(interaction, days_back)
            elif action == "view":
                if not event_id:
                    embed = discord.Embed(
                        title="❌ Missing Parameter",
                        description="Please provide an event_id to view",
                        color=0xff0000
                    )
                    await interaction.followup.send(embed=embed)
                    return
                await self._view_event_details(interaction, event_id)
            elif action == "create":
                if not event_name:
                    embed = discord.Embed(
                        title="❌ Missing Parameter",
                        description="Please provide an event_name for the new event",
                        color=0xff0000
                    )
                    await interaction.followup.send(embed=embed)
                    return
                await self._create_adhoc_event(interaction, event_name)
            elif action == "delete":
                if not event_id:
                    embed = discord.Embed(
                        title="❌ Missing Parameter",
                        description="Please provide an event_id to delete",
                        color=0xff0000
                    )
                    await interaction.followup.send(embed=embed)
                    return
                await self._delete_event(interaction, event_id)
                
        except Exception as e:
            print(f"❌ Error in event command: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            
            embed = discord.Embed(
                title="❌ Command Error",
                description=f"An error occurred: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)

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
