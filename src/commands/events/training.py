"""
Training Events Management Commands
Handles training-related event creation, deletion, and viewing
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging

from database.operations import get_all_events, create_event, delete_event

logger = logging.getLogger(__name__)

class TrainingEvents(commands.Cog):
    """Training event management commands"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("TrainingEvents cog initialized")

    @app_commands.command(name="red-training-create", description="Create a new training event")
    @app_commands.describe(
        name="Name of the training event",
        description="Description of the training event", 
        date="Date of the event (YYYY-MM-DD)",
        time="Time of the event (HH:MM)",
        training_type="Type of training event"
    )
    @app_commands.choices(training_type=[
        app_commands.Choice(name="Flight Training", value="flight_training"),
        app_commands.Choice(name="Combat Training", value="combat_training"),
        app_commands.Choice(name="Mining Training", value="mining_training"),
        app_commands.Choice(name="Ship Operations", value="ship_ops"),
        app_commands.Choice(name="Navigation", value="navigation"),
        app_commands.Choice(name="Other", value="other")
    ])
    async def create_training_event(
        self, 
        interaction: discord.Interaction, 
        name: str, 
        description: str,
        date: str,
        time: str,
        training_type: app_commands.Choice[str]
    ):
        """Create a new training event"""
        try:
            # Create event with training category
            event_id = await create_event(
                name=name,
                description=description,
                category="training",
                subcategory=training_type.value,
                date=date,
                time=time,
                created_by=interaction.user.id,
                guild_id=str(interaction.guild.id)
            )
            
            embed = discord.Embed(
                title="📚 Training Event Created",
                description=f"**{name}** has been scheduled",
                color=0x4CAF50
            )
            embed.add_field(name="Type", value=training_type.name, inline=True)
            embed.add_field(name="Date", value=date, inline=True)
            embed.add_field(name="Time", value=time, inline=True)
            embed.add_field(name="Description", value=description, inline=False)
            embed.add_field(name="Event ID", value=str(event_id), inline=True)
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Training event created: {name} (ID: {event_id}, Type: {training_type.value})")
            
        except Exception as e:
            logger.error(f"Error creating training event: {e}")
            await interaction.response.send_message(
                "❌ Failed to create training event. Please try again later.",
                ephemeral=True
            )

    @app_commands.command(name="red-training-delete", description="Delete a training event")
    @app_commands.describe(event_id="ID of the training event to delete")
    async def delete_training_event(self, interaction: discord.Interaction, event_id: int):
        """Delete a training event"""
        try:
            # Verify event exists and is training category
            events = await get_all_events(category="training", guild_id=str(interaction.guild.id))
            training_event = None
            for event in events:
                if event['id'] == event_id and event['category'] == 'training':
                    training_event = event
                    break
            
            if not training_event:
                await interaction.response.send_message(
                    "❌ Training event not found or you don't have permission to delete it.",
                    ephemeral=True
                )
                return
            
            await delete_event(event_id, guild_id=str(interaction.guild.id))
            
            embed = discord.Embed(
                title="🗑️ Training Event Deleted",
                description=f"**{training_event['name']}** has been deleted",
                color=0xff0000
            )
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Training event deleted: {training_event['name']} (ID: {event_id})")
            
        except Exception as e:
            logger.error(f"Error deleting training event: {e}")
            await interaction.response.send_message(
                "❌ Failed to delete training event. Please try again later.",
                ephemeral=True
            )

    @app_commands.command(name="red-training-view", description="View all training events")
    async def view_training_events(self, interaction: discord.Interaction):
        """View all training events"""
        try:
            events = await get_all_events(category="training", guild_id=str(interaction.guild.id))
            training_events = [event for event in events if event['category'] == 'training']
            
            if not training_events:
                await interaction.response.send_message(
                    "📅 No training events scheduled yet.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="📚 Scheduled Training Events",
                color=0x4CAF50
            )
            
            for event in training_events[:10]:  # Limit to 10 events
                subcategory = event.get('subcategory', 'Unknown')
                embed.add_field(
                    name=f"{event['name']} (ID: {event['id']})",
                    value=f"📖 {subcategory.replace('_', ' ').title()}\n📅 {event['date']} at {event['time']}\n{event['description']}",
                    inline=False
                )
            
            if len(training_events) > 10:
                embed.set_footer(text=f"Showing 10 of {len(training_events)} events")
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Training events viewed by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error viewing training events: {e}")
            await interaction.response.send_message(
                "❌ Failed to load training events. Please try again later.",
                ephemeral=True
            )

async def setup(bot):
    """Setup function to add the cog to the bot"""
    logger.info("Setting up TrainingEvents cog...")
    await bot.add_cog(TrainingEvents(bot))
    logger.info("TrainingEvents cog added successfully")
