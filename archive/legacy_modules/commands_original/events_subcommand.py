"""
Red Legion Event Management System with Discord Subcommand Groups.

This module implements a professional event management system using Discord's
recommended subcommand group architecture for optimal organization and UX.

Structure:
- /redevents create <category> <name> [description]
- /redevents delete <event_id>
- /redevents view [category] [status] [event_id]
- /redevents list [category] [status]
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
from typing import Optional
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import operations as database_operations


class RedEventsGroup(app_commands.Group):
    """Red Legion Events command group with subcommands."""
    
    def __init__(self):
        super().__init__(
            name="redevents",
            description="Red Legion event management system"
        )

    @app_commands.command(name="create", description="Create a new Red Legion event")
    @app_commands.describe(
        category="Event category",
        name="Event name (required)",
        description="Event description (optional)"
    )
    @app_commands.choices(category=[
        app_commands.Choice(name="Mining Operations", value="mining"),
        app_commands.Choice(name="Combat Training", value="combat"),
        app_commands.Choice(name="Flight Training", value="training"),
        app_commands.Choice(name="Salvage Operations", value="salvage"),
        app_commands.Choice(name="Exploration", value="exploration"),
        app_commands.Choice(name="Miscellaneous", value="misc")
    ])
    async def create_event(
        self,
        interaction: discord.Interaction,
        category: app_commands.Choice[str],
        name: str,
        description: Optional[str] = None
    ):
        """Create a new event in the specified category."""
        await interaction.response.defer()
        
        try:
            await self._create_event_by_category(
                interaction, 
                category.value, 
                name, 
                description
            )
        except Exception as e:
            print(f"❌ Error in create event command: {e}")
            embed = discord.Embed(
                title="❌ Command Error",
                description=f"An error occurred while creating the event: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="delete", description="Delete a Red Legion event (Admin only)")
    @app_commands.describe(event_id="ID of the event to delete")
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

    @app_commands.command(name="view", description="View detailed information about a specific event")
    @app_commands.describe(event_id="Specific event ID to view details")
    async def view_event(
        self,
        interaction: discord.Interaction,
        event_id: int
    ):
        """View detailed information about a specific event."""
        await interaction.response.defer()
        
        try:
            await self._view_event_details(interaction, event_id)
        except Exception as e:
            print(f"❌ Error in view event command: {e}")
            embed = discord.Embed(
                title="❌ Command Error",
                description=f"An error occurred while viewing the event: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="list", description="List Red Legion events with optional filters")
    @app_commands.describe(
        category="Event category to filter by (optional)",
        status="Event status to filter by (optional)"
    )
    @app_commands.choices(category=[
        app_commands.Choice(name="All Categories", value="all"),
        app_commands.Choice(name="Mining Operations", value="mining"),
        app_commands.Choice(name="Combat Training", value="combat"),
        app_commands.Choice(name="Flight Training", value="training"),
        app_commands.Choice(name="Salvage Operations", value="salvage"),
        app_commands.Choice(name="Exploration", value="exploration"),
        app_commands.Choice(name="Miscellaneous", value="misc")
    ], status=[
        app_commands.Choice(name="All Statuses", value="all"),
        app_commands.Choice(name="Active", value="active"),
        app_commands.Choice(name="Upcoming", value="upcoming"),
        app_commands.Choice(name="Completed", value="completed"),
        app_commands.Choice(name="Cancelled", value="cancelled")
    ])
    async def list_events(
        self,
        interaction: discord.Interaction,
        category: Optional[app_commands.Choice[str]] = None,
        status: Optional[app_commands.Choice[str]] = None
    ):
        """List events with optional filtering by category and status."""
        await interaction.response.defer()
        
        try:
            category_value = category.value if category else "all"
            status_value = status.value if status else "all"
            await self._lookup_events_by_filters(interaction, category_value, status_value)
        except Exception as e:
            print(f"❌ Error in list events command: {e}")
            embed = discord.Embed(
                title="❌ Command Error",
                description=f"An error occurred while listing events: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)

    # Implementation methods
    async def _create_event_by_category(self, interaction: discord.Interaction, category: str, name: str, description: str = None):
        """Create a new event in the specified category."""
        
        guild_id = str(interaction.guild.id)
        
        try:
            # Use modern event creation with category support
            # Default to tomorrow's date and current time for now
            from datetime import datetime, timedelta
            default_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            default_time = datetime.now().strftime('%H:%M')
            
            event_id = await database_operations.create_event(
                name=name,
                description=description or f"{category.title()} event created by {interaction.user.display_name}",
                category=category,
                date=default_date,
                time=default_time,
                created_by=interaction.user.id,
                guild_id=guild_id
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
                          f"**Status:** Planned\n"
                          f"**Organizer:** {interaction.user.display_name}",
                    inline=False
                )
                
                embed.add_field(
                    name="🎮 Next Steps",
                    value="• Use `/redevents list` to view all events\n"
                          "• Use `/redevents view` to view detailed information\n"
                          f"• Use `/redevents view event_id:{event_id}` for details",
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
        
        guild_id = str(interaction.guild.id)
        
        try:
            # First get event details for confirmation using new async function
            events = await database_operations.get_all_events(guild_id=guild_id)
            event_to_delete = None
            
            for event in events:
                if event.get('event_id') == event_id:
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
            event_name = event_to_delete.get('name', 'Unknown Event')
            view = DeleteConfirmationView(event_id, event_name)
            
            embed = discord.Embed(
                title="⚠️ Confirm Event Deletion",
                description=f"Are you sure you want to delete this event?\n\n"
                           f"**Event Name:** {event_name}\n"
                           f"**Event ID:** {event_id}\n"
                           f"**Category:** {event_to_delete.get('event_type', 'Unknown')}\n"
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

    async def _view_event_details(self, interaction: discord.Interaction, event_id: int):
        """View detailed information about a specific event."""
        
        guild_id = str(interaction.guild.id)
        
        try:
            # Get all events and find the specific one using new async function
            events = await database_operations.get_all_events(guild_id=guild_id)
            target_event = None
            
            for event in events:
                if event.get('event_id') == event_id:
                    target_event = event
                    break
            
            if not target_event:
                embed = discord.Embed(
                    title="❌ Event Not Found",
                    description=f"No event found with ID {event_id}",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Extract event details from the dictionary
            event_name = target_event.get('name', 'Unknown Event')
            event_description = target_event.get('description', 'No description provided')
            event_type = target_event.get('event_type', 'Unknown')
            status = target_event.get('status', 'Unknown')
            start_time = target_event.get('start_time')
            organizer_name = target_event.get('organizer_name', 'Unknown')
            
            # Create detailed embed
            embed = discord.Embed(
                title="📋 Event Details",
                description=f"**{event_name}**",
                color=0x0099ff
            )
            
            embed.add_field(
                name="🆔 Event Information",
                value=f"**ID:** {event_id}\n"
                      f"**Category:** {event_type.title()}\n"
                      f"**Status:** {status.title()}\n"
                      f"**Creator:** {organizer_name}",
                inline=True
            )
            
            embed.add_field(
                name="⏰ Timing",
                value=f"**Start:** {start_time.strftime('%Y-%m-%d %H:%M UTC') if start_time else 'TBD'}",
                inline=True
            )
            
            embed.add_field(
                name="📝 Description",
                value=event_description,
                inline=False
            )
            
            embed.add_field(
                name="🎮 Actions",
                value="• Use `/redevents list` to view all events\n"
                      "• Administrators can use `/redevents delete` to remove this event",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Error viewing event details: {e}")
            embed = discord.Embed(
                title="❌ Database Error",
                description=f"Could not retrieve event details: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)

    async def _lookup_events_by_filters(self, interaction: discord.Interaction, category: str, status: str):
        """Look up events by category and status filters."""
        
        guild_id = str(interaction.guild.id)
        
        try:
            # Get events using new async function with category filter
            if category != "all":
                events = await database_operations.get_all_events(category=category, guild_id=guild_id)
            else:
                events = await database_operations.get_all_events(guild_id=guild_id)
            
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
            
            # Filter by status if not "all"
            if status != "all":
                events = [e for e in events if e.get('status') == status]
            
            # Create embed with event list
            embed = discord.Embed(
                title="📋 Event List",
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
                event_id = event.get('event_id')
                event_name = event.get('name', 'Unknown Event')
                event_status = event.get('status', 'unknown')
                event_type = event.get('event_type', 'unknown')
                start_time = event.get('start_time')
                
                if start_time:
                    start_date = start_time.strftime('%Y-%m-%d') if hasattr(start_time, 'strftime') else str(start_time)
                else:
                    start_date = 'TBD'
                
                status_emoji = "🟢" if event_status == "active" else "🔴" if event_status == "completed" else "🟡"
                events_text.append(f"{status_emoji} **{event_name}** (ID: {event_id})\n   Category: {event_type.title()} | Status: {event_status.title()} | Date: {start_date}")
            
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
                value="Use `/redevents view event_id:<id>` to view detailed information about a specific event.",
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


class DeleteConfirmationView(discord.ui.View):
    """Confirmation view for event deletion."""
    
    def __init__(self, event_id: int, event_name: str):
        super().__init__(timeout=300)
        self.event_id = event_id
        self.event_name = event_name
    
    @discord.ui.button(label='Confirm Delete', style=discord.ButtonStyle.danger, emoji='🗑️')
    async def confirm_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle confirmed deletion."""
        
        guild_id = str(interaction.guild.id)
        
        try:
            # Actually delete the event using new async function
            success = await database_operations.delete_event(self.event_id, guild_id)
            
            if success:
                embed = discord.Embed(
                    title="✅ Event Deleted",
                    description=f"Successfully deleted event '{self.event_name}' (ID: {self.event_id})",
                    color=0x00aa00
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


class EventManagement(commands.Cog):
    """Event Management Cog using Discord subcommand groups."""
    
    def __init__(self, bot):
        self.bot = bot
    
    # Properly register the command group
    redevents = RedEventsGroup()


async def setup(bot):
    """Setup function for discord.py extension loading."""
    print("🔧 Setting up Event Management with subcommand groups...")
    try:
        cog = EventManagement(bot)
        await bot.add_cog(cog)
        print("✅ Event Management cog loaded with subcommand groups")
        print("✅ Available commands:")
        print("   • /redevents create <category> <name> [description]")
        print("   • /redevents delete <event_id>")
        print("   • /redevents view <event_id>")
        print("   • /redevents list [category] [status]")
    except Exception as e:
        print(f"❌ Error in setup function: {e}")
        import traceback
        traceback.print_exc()
