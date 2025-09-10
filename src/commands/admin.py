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
                title="🗑️ Delete Event",
                description="⚠️ **WARNING: This action cannot be undone!**\n\n"
                           "Select an event to delete from the dropdown below.\n"
                           "This will permanently remove:\n"
                           "• The event record\n"
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
            placeholder="Select an event to delete...",
            options=options,
            min_values=1,
            max_values=1
        )
    
    async def callback(self, interaction: discord.Interaction):
        selected_event_id = self.values[0]
        
        # Find the selected event
        selected_event = None
        for event in self.events:
            if event['event_id'] == selected_event_id:
                selected_event = event
                break
        
        if not selected_event:
            await interaction.response.send_message(
                "❌ Selected event not found.",
                ephemeral=True
            )
            return
        
        # Show confirmation modal
        modal = EventDeleteConfirmationModal(selected_event)
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


async def setup(bot):
    """Setup function for discord.py extension loading."""
    await bot.add_cog(AdminCommands(bot))