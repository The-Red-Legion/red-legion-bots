"""
Voice channel participation tracking for the Red Legion Discord bot.

This module handles voice state updates and member tracking for events.
"""

import discord
from discord.ext import tasks
import asyncio
from datetime import datetime


# Global variables for tracking voice state
active_voice_channels = {}
member_times = {}
last_checks = {}


async def on_voice_state_update(member, before, after):
    """
    Handle voice state updates for participation tracking.
    
    Args:
        member: The Discord member
        before: Previous voice state
        after: New voice state
    """
    # Get current time
    now = datetime.now()
    
    # Handle member leaving voice channel
    if before.channel and before.channel.id in active_voice_channels:
        if member.id in member_times:
            # Calculate duration in the channel
            start_time = member_times[member.id]
            duration = (now - start_time).total_seconds()
            
            # Save participation if they were in for more than 30 seconds
            if duration > 30:
                try:
                    from ..database import save_participation
                    from ..config import get_database_url
                    from ..discord_utils import has_org_role
                    
                    db_url = get_database_url()
                    if db_url:
                        # Check if member has org role
                        is_org_member = has_org_role(member)
                        
                        save_participation(
                            db_url, 
                            before.channel.id, 
                            member.id, 
                            member.display_name, 
                            int(duration), 
                            is_org_member
                        )
                        print(f"Saved participation: {member.display_name} - {duration:.0f}s")
                except Exception as e:
                    print(f"Error saving participation for {member.display_name}: {e}")
            
            # Remove from tracking
            del member_times[member.id]
    
    # Handle member joining voice channel
    if after.channel and after.channel.id in active_voice_channels:
        # Start tracking this member
        member_times[member.id] = now
        print(f"Started tracking: {member.display_name} in {after.channel.name}")


@tasks.loop(minutes=5)
async def log_members():
    """
    Periodic task to log current voice channel members.
    Runs every 5 minutes to ensure participation is tracked even for long sessions.
    """
    now = datetime.now()
    
    for channel_id in list(active_voice_channels.keys()):
        try:
            # Get the bot instance to access channels
            from ..participation_bot import bot  # This will need to be passed differently
            
            channel = bot.get_channel(channel_id)
            if not channel:
                # Channel no longer exists, remove from tracking
                del active_voice_channels[channel_id]
                continue
            
            # Log current members in the channel
            current_members = [member for member in channel.members if not member.bot]
            
            if current_members:
                print(f"Channel {channel.name} has {len(current_members)} members:")
                for member in current_members:
                    if member.id in member_times:
                        duration = (now - member_times[member.id]).total_seconds()
                        print(f"  - {member.display_name}: {duration:.0f}s")
                    else:
                        # Member was already in channel when tracking started
                        member_times[member.id] = now
                        print(f"  - {member.display_name}: started tracking")
            
            # Update last check time
            last_checks[channel_id] = now
            
        except Exception as e:
            print(f"Error in log_members for channel {channel_id}: {e}")


def start_voice_tracking():
    """Start the voice tracking background task."""
    if not log_members.is_running():
        log_members.start()
        print("✅ Voice tracking task started")


def stop_voice_tracking():
    """Stop the voice tracking background task."""
    if log_members.is_running():
        log_members.cancel()
        print("⏹️ Voice tracking task stopped")


def add_tracked_channel(channel_id):
    """
    Add a voice channel to participation tracking.
    
    Args:
        channel_id: The Discord channel ID to track
    """
    active_voice_channels[channel_id] = datetime.now()
    last_checks[channel_id] = datetime.now()
    print(f"Added channel {channel_id} to voice tracking")


def remove_tracked_channel(channel_id):
    """
    Remove a voice channel from participation tracking.
    
    Args:
        channel_id: The Discord channel ID to stop tracking
    """
    if channel_id in active_voice_channels:
        del active_voice_channels[channel_id]
    
    if channel_id in last_checks:
        del last_checks[channel_id]
    
    # Clean up member times for this channel
    # Note: This is simplified - in practice we'd need to track which channel each member is in
    print(f"Removed channel {channel_id} from voice tracking")


def get_tracking_status():
    """
    Get current voice tracking status.
    
    Returns:
        dict: Status information about tracked channels and members
    """
    return {
        'tracked_channels': len(active_voice_channels),
        'tracked_members': len(member_times),
        'task_running': log_members.is_running()
    }
