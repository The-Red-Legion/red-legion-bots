"""
Mining Events Management Commands
Handles mining-related event creation, deletion, and viewing
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging

from config.settings import GUILD_ID
from database.operations import get_all_events, create_event, delete_event

logger = logging.getLogger(__name__)

class MiningEvents(commands.Cog):
    """Mining event management commands"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("MiningEvents cog initialized")

    @app_commands.command(name="red-mining-create", description="Create a new mining event")
    @app_commands.describe(
        name="Name of the mining event",
        description="Description of the mining event",
        date="Date of the event (YYYY-MM-DD)",
        time="Time of the event (HH:MM)"
    )
    async def create_mining_event(
        self, 
        interaction: discord.Interaction, 
        name: str, 
        description: str,
        date: str,
        time: str
    ):
        """Create a new mining event"""
        try:
            # Create event with mining category
            event_id = await create_event(
                name=name,
                description=description,
                category="mining",
                date=date,
                time=time,
                created_by=interaction.user.id
            )
            
            embed = discord.Embed(
                title="✅ Mining Event Created",
                description=f"**{name}** has been scheduled",
                color=0x00ff00
            )
            embed.add_field(name="Date", value=date, inline=True)
            embed.add_field(name="Time", value=time, inline=True)
            embed.add_field(name="Description", value=description, inline=False)
            embed.add_field(name="Event ID", value=str(event_id), inline=True)
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Mining event created: {name} (ID: {event_id})")
            
        except Exception as e:
            logger.error(f"Error creating mining event: {e}")
            await interaction.response.send_message(
                "❌ Failed to create mining event. Please try again later.",
                ephemeral=True
            )

    @app_commands.command(name="red-mining-delete", description="Delete a mining event")
    @app_commands.describe(event_id="ID of the mining event to delete")
    async def delete_mining_event(self, interaction: discord.Interaction, event_id: int):
        """Delete a mining event"""
        try:
            # Verify event exists and is mining category
            events = await get_all_events()
            mining_event = None
            for event in events:
                if event['id'] == event_id and event['category'] == 'mining':
                    mining_event = event
                    break
            
            if not mining_event:
                await interaction.response.send_message(
                    "❌ Mining event not found or you don't have permission to delete it.",
                    ephemeral=True
                )
                return
            
            await delete_event(event_id)
            
            embed = discord.Embed(
                title="🗑️ Mining Event Deleted",
                description=f"**{mining_event['name']}** has been deleted",
                color=0xff0000
            )
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Mining event deleted: {mining_event['name']} (ID: {event_id})")
            
        except Exception as e:
            logger.error(f"Error deleting mining event: {e}")
            await interaction.response.send_message(
                "❌ Failed to delete mining event. Please try again later.",
                ephemeral=True
            )

    @app_commands.command(name="red-mining-view", description="View all mining events")
    async def view_mining_events(self, interaction: discord.Interaction):
        """View all mining events"""
        try:
            events = await get_all_events()
            mining_events = [event for event in events if event['category'] == 'mining']
            
            if not mining_events:
                await interaction.response.send_message(
                    "📅 No mining events scheduled yet.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="⛏️ Scheduled Mining Events",
                color=0x0099ff
            )
            
            for event in mining_events[:10]:  # Limit to 10 events
                embed.add_field(
                    name=f"{event['name']} (ID: {event['id']})",
                    value=f"📅 {event['date']} at {event['time']}\n{event['description']}",
                    inline=False
                )
            
            if len(mining_events) > 10:
                embed.set_footer(text=f"Showing 10 of {len(mining_events)} events")
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Mining events viewed by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error viewing mining events: {e}")
            await interaction.response.send_message(
                "❌ Failed to load mining events. Please try again later.",
                ephemeral=True
            )

async def setup(bot):
    """Setup function to add the cog to the bot"""
    logger.info("Setting up MiningEvents cog...")
    await bot.add_cog(MiningEvents(bot), guild=discord.Object(id=GUILD_ID))
    logger.info("MiningEvents cog added successfully")
