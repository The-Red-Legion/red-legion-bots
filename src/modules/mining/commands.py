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

class MiningCommands(commands.GroupCog, name="mining", description="Mining operations and session management"):
    """Mining operations command group."""
    
    def __init__(self, bot):
        self.bot = bot
        self.event_manager = MiningEventManager()
        self.voice_tracker = VoiceTracker(bot)
        super().__init__()
        
    @app_commands.command(name="start", description="Start a mining session with voice channel tracking")
    async def start_mining(
        self, 
        interaction: discord.Interaction
    ):
        """Start a new mining session."""
        # Show mining session start modal
        modal = MiningStartModal(self.event_manager, self.voice_tracker, self.bot)
        await interaction.response.send_modal(modal)
    
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
            
            # Auto-leave the Dispatch/Main channel when mining session ends
            try:
                # Get the Dispatch channel ID and leave it
                channels = get_sunday_mining_channels(guild_id)
                dispatch_channel_id = channels.get('dispatch')
                if dispatch_channel_id:
                    dispatch_channel_id = int(dispatch_channel_id)
                    leave_success = await self.voice_tracker.leave_voice_channel(dispatch_channel_id)
                    
                    if leave_success:
                        print(f"✅ Bot left Dispatch channel after mining event {active_event['event_id']}")
                    else:
                        print(f"⚠️ Could not leave Dispatch channel after mining event {active_event['event_id']}")
                        
            except Exception as e:
                print(f"❌ Error auto-leaving voice channel: {e}")
                # Don't fail the entire mining stop - just log the issue
            
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
            
            # Also get current voice channel participants for a complete picture
            channels = get_sunday_mining_channels(guild_id)
            current_voice_participants = await self._get_current_voice_participants(interaction.guild, channels)
            total_current_voice = sum(len(members) for members in current_voice_participants.values())
            
            embed = discord.Embed(
                title="🏁 Mining Session Ended",
                description=f"Session **{active_event['event_id']}** has been closed",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            # Enhanced final stats
            duration_minutes = stats.get('duration_minutes', 0)
            total_participants = stats.get('total_participants', 0)
            max_concurrent = max(stats.get('max_concurrent', 0), total_current_voice)
            
            # If no participation records yet but people are in voice, show current count
            if total_participants == 0 and total_current_voice > 0:
                total_participants = total_current_voice
            
            embed.add_field(
                name="📊 Final Stats",
                value=f"**Duration:** {duration_minutes} minutes\n"
                      f"**Total Participants:** {total_participants}\n"
                      f"**Max Concurrent:** {max_concurrent}",
                inline=False
            )
            
            # Show current voice participants if any
            if current_voice_participants:
                participant_text = []
                for channel_name, members in current_voice_participants.items():
                    if members:
                        member_names = [member.display_name for member in members]
                        participant_text.append(f"**{channel_name}:** {', '.join(member_names)}")
                
                if participant_text:
                    embed.add_field(
                        name="🎤 Still in Voice Channels",
                        value="\n".join(participant_text) + f"\n\n*These members were still in channels when session ended*",
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
    
    async def _get_current_voice_participants(self, guild, channels):
        """Get current participants in mining voice channels."""
        try:
            current_participants = {}
            
            # Check each mining channel for current members
            for channel_key, channel_id_str in channels.items():
                try:
                    channel_id = int(channel_id_str)
                    voice_channel = guild.get_channel(channel_id)
                    
                    if voice_channel and hasattr(voice_channel, 'members'):
                        # Get members in this voice channel (excluding bots)
                        members_in_channel = [member for member in voice_channel.members if not member.bot]
                        
                        if members_in_channel:
                            # Use a friendly channel name
                            friendly_name = channel_key.title()
                            if channel_key == 'dispatch':
                                friendly_name = 'Dispatch/Main'
                            elif channel_key.startswith('group') or len(channel_key) <= 2:
                                friendly_name = f"Group {channel_key.upper()}"
                            
                            current_participants[friendly_name] = members_in_channel
                            
                except (ValueError, AttributeError) as e:
                    print(f"Warning: Could not check channel {channel_key}: {e}")
                    continue
            
            return current_participants
            
        except Exception as e:
            print(f"Error getting current voice participants: {e}")
            return {}


class MiningStartModal(discord.ui.Modal):
    """Modal for mining session startup information."""
    
    def __init__(self, event_manager, voice_tracker, bot):
        super().__init__(title='Start Mining Session')
        self.event_manager = event_manager
        self.voice_tracker = voice_tracker
        self.bot = bot
        
        # Location input
        self.location = discord.ui.TextInput(
            label='Mining Location',
            placeholder='e.g., Daymar, Lyria, Aaron Halo',
            required=False,
            max_length=100
        )
        self.add_item(self.location)
        
        # Notes input
        self.notes = discord.ui.TextInput(
            label='Session Notes',
            placeholder='Optional notes about this mining session',
            required=False,
            style=discord.TextStyle.paragraph,
            max_length=500
        )
        self.add_item(self.notes)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            guild_id = interaction.guild_id
            organizer = interaction.user
            
            # Create mining event in database
            event_result = await self.event_manager.create_event(
                guild_id=guild_id,
                organizer_id=organizer.id,
                organizer_name=organizer.display_name,
                location=self.location.value if self.location.value else None,
                notes=self.notes.value if self.notes.value else None
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
            
            # Auto-join the Dispatch/Main channel to indicate mining session is active
            voice_join_status = "⚠️ Skipped - no dispatch channel configured"
            try:
                # Get the Dispatch channel ID
                dispatch_channel_id = channels.get('dispatch')
                if dispatch_channel_id:
                    dispatch_channel_id = int(dispatch_channel_id)
                    join_success = await self.voice_tracker.join_voice_channel(dispatch_channel_id)
                    
                    if join_success:
                        voice_join_status = "✅ Bot joined dispatch channel successfully"
                        print(f"✅ Bot joined Dispatch channel for mining event {event_data['event_id']}")
                    else:
                        voice_join_status = "❌ Bot failed to join dispatch channel"
                        print(f"⚠️ Could not join Dispatch channel for mining event {event_data['event_id']}")
                else:
                    print("⚠️ No Dispatch channel configured - skipping auto-join")
                    
            except Exception as e:
                voice_join_status = f"❌ Error joining dispatch channel: {str(e)[:50]}"
                print(f"❌ Error auto-joining voice channel: {e}")
                # Don't fail the entire mining start - just log the issue
            
            # Get current voice participants for initial display
            guild = interaction.guild
            current_voice_participants = await self._get_current_voice_participants(guild, channels)
            total_current_voice = sum(len(members) for members in current_voice_participants.values())
            
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
                      f"**Location:** {self.location.value or 'Not specified'}\n" 
                      f"**Started:** <t:{int(datetime.now().timestamp())}:R>",
                inline=False
            )
            
            # Add tracked channels information
            tracked_channels_info = []
            voice_channel_names = []
            if channels:
                for channel_name, channel_id_str in channels.items():
                    if channel_name == 'dispatch':
                        continue  # Skip dispatch channel in voice tracking list
                    
                    try:
                        vc = guild.get_channel(int(channel_id_str))
                        if vc:
                            voice_channel_names.append(f"`{vc.name}`")
                            # Show current participants in this channel
                            if channel_name in current_voice_participants and current_voice_participants[channel_name]:
                                member_count = len(current_voice_participants[channel_name])
                                tracked_channels_info.append(f"🎤 **{vc.name}**: {member_count} active")
                            else:
                                tracked_channels_info.append(f"🎤 **{vc.name}**: Empty")
                    except (ValueError, AttributeError):
                        continue  # Skip invalid channel IDs
            
            embed.add_field(
                name="🎤 Voice Tracking & Bot Presence",
                value=f"• Bot will track participation in mining voice channels\n"
                      f"• Dispatch channel: {voice_join_status}\n"
                      f"• Join any mining channel to start earning participation time!",
                inline=False
            )
            
            # Add tracked channels and current participants
            if tracked_channels_info:
                embed.add_field(
                    name="📡 Tracked Voice Channels",
                    value="\n".join(tracked_channels_info),
                    inline=True
                )
            
            # Show current active participants
            if total_current_voice > 0:
                # Get all current participants across channels
                all_current_participants = set()
                for members in current_voice_participants.values():
                    for member in members:
                        all_current_participants.add(member.display_name)
                
                participants_list = sorted(list(all_current_participants))
                if len(participants_list) <= 8:
                    participants_text = ", ".join(participants_list)
                else:
                    participants_text = ", ".join(participants_list[:8]) + f" (+{len(participants_list)-8} more)"
                
                embed.add_field(
                    name="👥 Currently in Voice",
                    value=f"**{total_current_voice} participants active**\n{participants_text}",
                    inline=True
                )
            else:
                embed.add_field(
                    name="👥 Currently in Voice",
                    value="No participants currently in tracked channels",
                    inline=True
                )
            
            # Add next steps and notes
            embed.add_field(
                name="🚀 Next Steps",
                value="• Join voice channels to participate and earn time\n"
                      "• Use `/mining stop` when the session ends\n"
                      "• Use `/payroll status` to see upcoming payroll calculations",
                inline=False
            )
            
            if self.notes.value:
                embed.add_field(
                    name="📝 Session Notes",
                    value=self.notes.value[:1000],  # Limit notes length
                    inline=False
                )
            
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
    
    async def _get_current_voice_participants(self, guild, channels):
        """Helper method to get current voice participants - moved from main class."""
        try:
            current_participants = {}
            
            # Check each mining channel for current members
            for channel_key, channel_id_str in channels.items():
                try:
                    channel_id = int(channel_id_str)
                    voice_channel = guild.get_channel(channel_id)
                    
                    if voice_channel and hasattr(voice_channel, 'members'):
                        # Get members in this voice channel (excluding bots)
                        members_in_channel = [member for member in voice_channel.members if not member.bot]
                        
                        if members_in_channel:
                            # Use a friendly channel name
                            friendly_name = channel_key.title()
                            if channel_key == 'dispatch':
                                friendly_name = 'Dispatch/Main'
                            elif channel_key.startswith('group') or len(channel_key) <= 2:
                                friendly_name = f"Group {channel_key.upper()}"
                            
                            current_participants[friendly_name] = members_in_channel
                            
                except (ValueError, AttributeError) as e:
                    print(f"Warning: Could not check channel {channel_key}: {e}")
                    continue
            
            return current_participants
            
        except Exception as e:
            print(f"Error getting current voice participants: {e}")
            return {}


async def setup(bot):
    """Setup function for discord.py extension loading."""
    await bot.add_cog(MiningCommands(bot))