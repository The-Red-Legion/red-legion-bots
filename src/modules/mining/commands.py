"""
Mining Commands for Red Legion Bot

Clean, unified mining commands that work any day of the week.
Uses event-centric database design with the unified schema.
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Optional
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import get_sunday_mining_channels, DISCORD_CONFIG
from .events import MiningEventManager
from .participation import VoiceTracker

class MiningCommands(commands.GroupCog, name="mining"):
    """
    Mining operations command group.
    
    Commands:
    - /mining start - Start a mining session with voice tracking
    - /mining stop - End the current mining session
    - /mining status - Show current session information
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.event_manager = MiningEventManager()
        self.voice_tracker = VoiceTracker(bot)
        super().__init__()
        
    @app_commands.command(name="start", description="Start a mining session with voice channel tracking")
    @app_commands.describe(
        location="Mining location (e.g., 'Daymar', 'Lyria', 'Aaron Halo')",
        notes="Optional notes about this mining session"
    )
    async def start_mining(
        self, 
        interaction: discord.Interaction,
        location: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """Start a new mining session."""
        await interaction.response.defer()
        
        try:
            guild_id = interaction.guild_id
            organizer = interaction.user
            
            # Create mining event in database
            event_result = await self.event_manager.create_event(
                guild_id=guild_id,
                organizer_id=organizer.id,
                organizer_name=organizer.display_name,
                location=location,
                notes=notes
            )
            
            if not event_result['success']:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ Failed to Start Mining Session",
                        description=event_result['error'],
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return
            
            event_data = event_result['event']
            
            # Start voice channel tracking
            channels = get_sunday_mining_channels(guild_id)
            tracking_result = await self.voice_tracker.start_tracking(
                event_id=event_data['event_id'],
                channels=channels
            )
            
            if not tracking_result['success']:
                # Clean up event if voice tracking fails
                await self.event_manager.close_event(event_data['event_id'])
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ Failed to Start Voice Tracking",
                        description=tracking_result['error'],
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return
            
            # Create success embed
            embed = discord.Embed(
                title="⛏️ Mining Session Started",
                description=f"Session **{event_data['event_id']}** is now active",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📋 Session Details",
                value=f"**Organizer:** {organizer.display_name}\n"
                      f"**Location:** {location or 'Not specified'}\n" 
                      f"**Started:** <t:{int(datetime.now().timestamp())}:R>",
                inline=False
            )
            
            embed.add_field(
                name="🎤 Voice Tracking",
                value="Bot will track participation in mining voice channels.\n"
                      "Join any mining channel to start earning participation time!",
                inline=False
            )
            
            embed.add_field(
                name="🔄 Next Steps",
                value="1. Join mining voice channels to track participation\n"
                      "2. Mine ore and collect materials\n"
                      "3. Use `/mining stop` when session is complete\n"
                      "4. Payroll officer uses `/payroll mining` to calculate distribution",
                inline=False
            )
            
            if notes:
                embed.add_field(name="📝 Notes", value=notes, inline=False)
            
            embed.set_footer(text=f"Event ID: {event_data['event_id']}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error Starting Mining Session", 
                    description=f"An unexpected error occurred: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
    
    @app_commands.command(name="stop", description="Stop the current mining session")
    async def stop_mining(self, interaction: discord.Interaction):
        """Stop the current mining session."""
        await interaction.response.defer()
        
        try:
            guild_id = interaction.guild_id
            user = interaction.user
            
            # Get active mining event
            active_event = await self.event_manager.get_active_event(guild_id)
            
            if not active_event:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ No Active Mining Session",
                        description="There is no mining session currently running.\n"
                                  "Use `/mining start` to begin a new session.",
                        color=discord.Color.orange()
                    ),
                    ephemeral=True
                )
                return
            
            # Stop voice tracking
            await self.voice_tracker.stop_tracking(active_event['event_id'])
            
            # Close the event
            close_result = await self.event_manager.close_event(
                event_id=active_event['event_id'],
                closed_by_id=user.id,
                closed_by_name=user.display_name
            )
            
            if not close_result['success']:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ Error Stopping Session",
                        description=close_result['error'],
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return
            
            # Get final participation stats
            stats = await self.event_manager.get_event_stats(active_event['event_id'])
            
            embed = discord.Embed(
                title="🏁 Mining Session Ended",
                description=f"Session **{active_event['event_id']}** has been closed",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📊 Final Stats",
                value=f"**Duration:** {stats.get('duration_minutes', 0)} minutes\n"
                      f"**Total Participants:** {stats.get('total_participants', 0)}\n"
                      f"**Max Concurrent:** {stats.get('max_concurrent', 0)}",
                inline=False
            )
            
            embed.add_field(
                name="💰 Next Steps",
                value="**Payroll Officer:** Use `/payroll mining` to:\n"
                      "• Select this completed session\n"
                      "• Enter ore collection data\n" 
                      "• Calculate fair distribution\n"
                      "• Generate payout summary",
                inline=False
            )
            
            embed.set_footer(text=f"Closed by {user.display_name}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error Stopping Mining Session",
                    description=f"An unexpected error occurred: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
    
    @app_commands.command(name="status", description="Show current mining session status")
    async def mining_status(self, interaction: discord.Interaction):
        """Show current mining session information."""
        await interaction.response.defer()
        
        try:
            guild_id = interaction.guild_id
            
            # Get active mining event
            active_event = await self.event_manager.get_active_event(guild_id)
            
            if not active_event:
                embed = discord.Embed(
                    title="ℹ️ No Active Mining Session",
                    description="There is no mining session currently running.",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="🚀 Start Mining", 
                    value="Use `/mining start` to begin a new session",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed)
                return
            
            # Get current participation stats
            stats = await self.event_manager.get_event_stats(active_event['event_id'])
            participants = await self.voice_tracker.get_current_participants(active_event['event_id'])
            
            embed = discord.Embed(
                title="⛏️ Active Mining Session",
                description=f"Session **{active_event['event_id']}** is running",
                color=discord.Color.green(),
                timestamp=datetime.fromisoformat(active_event['started_at'])
            )
            
            embed.add_field(
                name="📋 Session Info",
                value=f"**Organizer:** {active_event['organizer_name']}\n"
                      f"**Location:** {active_event.get('location_notes', 'Not specified')}\n"
                      f"**Started:** <t:{int(datetime.fromisoformat(active_event['started_at']).timestamp())}:R>",
                inline=False
            )
            
            embed.add_field(
                name="📊 Current Stats", 
                value=f"**Active Participants:** {len(participants)}\n"
                      f"**Total Participants:** {stats.get('total_participants', 0)}\n"
                      f"**Session Duration:** {stats.get('duration_minutes', 0)} minutes",
                inline=False
            )
            
            if participants:
                participant_names = [p['display_name'] for p in participants[:10]]
                if len(participants) > 10:
                    participant_names.append(f"... and {len(participants) - 10} more")
                    
                embed.add_field(
                    name="👥 Currently Active",
                    value="\n".join(participant_names),
                    inline=False
                )
            
            embed.set_footer(text=f"Event ID: {active_event['event_id']}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error Getting Session Status",
                    description=f"An unexpected error occurred: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )


async def setup(bot):
    """Setup function for discord.py extension loading."""
    await bot.add_cog(MiningCommands(bot))