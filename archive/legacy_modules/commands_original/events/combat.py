"""
Combat Events Management Commands
Handles combat-related event creation, deletion, and viewing
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging

# Import from the operations.py file by avoiding the directory
from database import operations
get_all_events = operations.get_all_events
create_event = operations.create_event  
delete_event = operations.delete_event

logger = logging.getLogger(__name__)

class CombatEvents(commands.Cog):
    """Combat event management commands"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("CombatEvents cog initialized")

    @app_commands.command(name="redcombatcreate", description="Create a new combat event")
    @app_commands.describe(
        name="Name of the combat event",
        description="Description of the combat event", 
        date="Date of the event (YYYY-MM-DD)",
        time="Time of the event (HH:MM)",
        combat_type="Type of combat event"
    )
    @app_commands.choices(combat_type=[
        app_commands.Choice(name="PvP Training", value="pvp_training"),
        app_commands.Choice(name="PvE Mission", value="pve_mission"),
        app_commands.Choice(name="Fleet Operation", value="fleet_op"),
        app_commands.Choice(name="Boarding Practice", value="boarding"),
        app_commands.Choice(name="Other", value="other")
    ])
    async def create_combat_event(
        self, 
        interaction: discord.Interaction, 
        name: str, 
        description: str,
        date: str,
        time: str,
        combat_type: app_commands.Choice[str]
    ):
        """Create a new combat event"""
        try:
            # Create event with combat category
            event_id = await create_event(
                name=name,
                description=description,
                category="combat",
                subcategory=combat_type.value,
                date=date,
                time=time,
                created_by=interaction.user.id,
                guild_id=str(interaction.guild.id)
            )
            
            embed = discord.Embed(
                title="⚔️ Combat Event Created",
                description=f"**{name}** has been scheduled",
                color=0xff4444
            )
            embed.add_field(name="Type", value=combat_type.name, inline=True)
            embed.add_field(name="Date", value=date, inline=True)
            embed.add_field(name="Time", value=time, inline=True)
            embed.add_field(name="Description", value=description, inline=False)
            embed.add_field(name="Event ID", value=str(event_id), inline=True)
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Combat event created: {name} (ID: {event_id}, Type: {combat_type.value})")
            
        except Exception as e:
            logger.error(f"Error creating combat event: {e}")
            await interaction.response.send_message(
                "❌ Failed to create combat event. Please try again later.",
                ephemeral=True
            )

    @app_commands.command(name="redcombatdelete", description="Delete a combat event")
    @app_commands.describe(event_id="ID of the combat event to delete")
    async def delete_combat_event(self, interaction: discord.Interaction, event_id: int):
        """Delete a combat event"""
        try:
            # Verify event exists and is combat category
            events = await get_all_events(category="combat", guild_id=str(interaction.guild.id))
            combat_event = None
            for event in events:
                if event['id'] == event_id and event['category'] == 'combat':
                    combat_event = event
                    break
            
            if not combat_event:
                await interaction.response.send_message(
                    "❌ Combat event not found or you don't have permission to delete it.",
                    ephemeral=True
                )
                return
            
            await delete_event(event_id, guild_id=str(interaction.guild.id))
            
            embed = discord.Embed(
                title="🗑️ Combat Event Deleted",
                description=f"**{combat_event['name']}** has been deleted",
                color=0xff0000
            )
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Combat event deleted: {combat_event['name']} (ID: {event_id})")
            
        except Exception as e:
            logger.error(f"Error deleting combat event: {e}")
            await interaction.response.send_message(
                "❌ Failed to delete combat event. Please try again later.",
                ephemeral=True
            )

    @app_commands.command(name="redcombatview", description="View all combat events")
    async def view_combat_events(self, interaction: discord.Interaction):
        """View all combat events"""
        try:
            events = await get_all_events(category="combat", guild_id=str(interaction.guild.id))
            combat_events = [event for event in events if event['category'] == 'combat']
            
            if not combat_events:
                await interaction.response.send_message(
                    "📅 No combat events scheduled yet.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="⚔️ Scheduled Combat Events",
                color=0xff4444
            )
            
            for event in combat_events[:10]:  # Limit to 10 events
                subcategory = event.get('subcategory', 'Unknown')
                embed.add_field(
                    name=f"{event['name']} (ID: {event['id']})",
                    value=f"🎯 {subcategory.replace('_', ' ').title()}\n📅 {event['date']} at {event['time']}\n{event['description']}",
                    inline=False
                )
            
            if len(combat_events) > 10:
                embed.set_footer(text=f"Showing 10 of {len(combat_events)} events")
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Combat events viewed by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error viewing combat events: {e}")
            await interaction.response.send_message(
                "❌ Failed to load combat events. Please try again later.",
                ephemeral=True
            )

async def setup(bot):
    """Setup function to add the cog to the bot"""
    logger.info("Setting up CombatEvents cog...")
    await bot.add_cog(CombatEvents(bot))
    logger.info("CombatEvents cog added successfully")
