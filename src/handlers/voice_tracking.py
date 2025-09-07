"""
Voice channel participation tracking for the Red Legion Discord bot.

This module handles voice state updates and member tracking for events.
"""

import discord
from discord.ext import tasks
import asyncio
from datetime import datetime, timedelta


# Global variables for tracking voice state
active_voice_channels = {}
member_times = {}
last_checks = {}
bot_instance = None  # Store bot reference for voice operations
bot_voice_connections = {}  # Track bot's voice connections

# Enhanced tracking for Sunday mining sessions
member_session_data = {}  # {member_id: {'total_time': int, 'channels': {channel_id: time}, 'primary_channel': channel_id, 'session_start': datetime}}


async def _handle_voice_state_update(member, before, after):
    """
    Handle voice state updates for participation tracking.
    Enhanced to handle channel switching during mining sessions.
    
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
            
            # Update session tracking data
            if member.id not in member_session_data:
                member_session_data[member.id] = {
                    'total_time': 0,
                    'channels': {},
                    'primary_channel': before.channel.id,
                    'session_start': start_time
                }
            
            # Add time to this specific channel
            channel_id = str(before.channel.id)
            if channel_id not in member_session_data[member.id]['channels']:
                member_session_data[member.id]['channels'][channel_id] = 0
            member_session_data[member.id]['channels'][channel_id] += duration
            member_session_data[member.id]['total_time'] += duration
            
            # Update primary channel (channel with most time)
            primary_channel = max(
                member_session_data[member.id]['channels'].items(),
                key=lambda x: x[1]
            )[0]
            member_session_data[member.id]['primary_channel'] = primary_channel
            
            # Save participation if they were in for more than 30 seconds
            if duration > 30:
                try:
                    from database import save_mining_participation
                    from config.settings import get_database_url
                    from utils import has_org_role
                    from commands.mining import current_session
                    
                    db_url = get_database_url()
                    if db_url:
                        # Check if member has org role
                        is_org_member = has_org_role(member)
                        
                        # Get event_id from current active session
                        event_id = current_session.get('event_id') if current_session.get('active') else None
                        
                        if event_id:
                            # Calculate proper timestamps
                            end_time = now
                            start_time = end_time - timedelta(seconds=duration)
                            
                            # Save with enhanced data using new function signature
                            save_mining_participation(
                                db_url,
                                event_id,
                                member.id,
                                member.display_name,
                                before.channel.id,
                                before.channel.name,
                                start_time,
                                end_time,
                                int(duration),
                                is_org_member
                            )
                            print(f"✅ Saved participation: {member.display_name} - {duration:.0f}s in {before.channel.name} (Event ID: {event_id})")
                        else:
                            print(f"⚠️ No active mining event - not saving participation for {member.display_name}")
                        
                except Exception as e:
                    print(f"❌ Error saving participation for {member.display_name}: {e}")
            
            # Remove from current tracking but keep session data
            del member_times[member.id]
    
    # Handle member joining voice channel
    if after.channel and after.channel.id in active_voice_channels:
        # Start tracking this member
        member_times[member.id] = now
        
        # Initialize session data if needed
        if member.id not in member_session_data:
            member_session_data[member.id] = {
                'total_time': 0,
                'channels': {},
                'primary_channel': after.channel.id,
                'session_start': now
            }
        
        print(f"Started tracking: {member.display_name} in {after.channel.name}")
        
        # Log channel switch if this isn't their first channel
        if len(member_session_data[member.id]['channels']) > 0:
            print(f"Channel switch: {member.display_name} moved to {after.channel.name}")


def get_member_mining_summary(member_id, bot=None):
    """Get a summary of a member's mining session participation."""
    if member_id not in member_session_data:
        return None
    
    data = member_session_data[member_id]
    
    # Get channel names for display
    channel_breakdown = {}
    try:
        if bot:
            for channel_id, time_spent in data['channels'].items():
                channel = bot.get_channel(int(channel_id))
                channel_name = channel.name if channel else f"Channel {channel_id}"
                channel_breakdown[channel_name] = time_spent
        else:
            channel_breakdown = data['channels']
    except (AttributeError, ValueError):
        channel_breakdown = data['channels']
    
    return {
        'total_time': data['total_time'],
        'channel_breakdown': channel_breakdown,
        'primary_channel': data['primary_channel'],
        'session_start': data['session_start'],
        'session_duration': (datetime.now() - data['session_start']).total_seconds()
    }


def get_all_mining_participants(bot=None):
    """Get summary of all current mining participants."""
    participants = {}
    
    for member_id, data in member_session_data.items():
        try:
            if bot:
                member = bot.get_user(member_id)
                username = member.display_name if member else f"User {member_id}"
            else:
                username = f"User {member_id}"
        except (AttributeError):
            username = f"User {member_id}"
        
        participants[member_id] = {
            'username': username,
            'total_time': data['total_time'],
            'channel_count': len(data['channels']),
            'primary_channel': data['primary_channel']
        }
    
    return participants


def reset_mining_session():
    """Reset all mining session tracking data."""
    global member_session_data
    member_session_data = {}
    print("✅ Mining session tracking data reset")


@tasks.loop(minutes=5)
async def log_members():
    """
    Periodic task to log current voice channel members.
    Runs every 5 minutes to ensure participation is tracked even for long sessions.
    """
    # TODO: Implement proper bot context passing for background tasks
    # now = datetime.now()
    
    for channel_id in list(active_voice_channels.keys()):
        try:
            # Note: This function needs to be called with proper bot context
            # For now, we'll skip channel name resolution in background tasks
            # channel = bot.get_channel(channel_id) if bot else None
            # if not channel:
            #     # Channel no longer exists, remove from tracking
            #     del active_voice_channels[channel_id]
            #     continue
            
            # Skip channel validation for now since bot instance is not available
            # This is a background task limitation
            # TODO: Implement proper bot context passing for background tasks
            pass
            
            # The following code is commented out due to missing bot context
            # current_members = [member for member in channel.members if not member.bot]
            # 
            # if current_members:
            #     print(f"Channel {channel.name} has {len(current_members)} members:")
            #     for member in current_members:
            #         if member.id in member_times:
            #             duration = (now - member_times[member.id]).total_seconds()
            #             print(f"  - {member.display_name}: {duration:.0f}s")
            #         else:
            #             # Member was already in channel when tracking started
            #             member_times[member.id] = now
            #             print(f"  - {member.display_name}: started tracking")
            # 
            # # Update last check time
            # last_checks[channel_id] = now
            
        except Exception as e:
            print(f"Error in log_members for channel {channel_id}: {e}")


# Alias for backward compatibility
on_voice_state_update = _handle_voice_state_update


def start_voice_tracking():
    """Start the voice tracking background task."""
    if not log_members.is_running():
        log_members.start()
        print("✅ Voice tracking task started")


async def disconnect_from_all_channels():
    """Disconnect from all tracked voice channels."""
    global bot_voice_connections
    
    for channel_id in list(bot_voice_connections.keys()):
        await leave_voice_channel(channel_id)
    
    print("🔇 Disconnected from all voice channels")


def stop_voice_tracking():
    """Stop the voice tracking background task and disconnect from all voice channels."""
    if log_members.is_running():
        log_members.cancel()
        print("⏹️ Voice tracking task stopped")
    
    # Disconnect from all voice channels
    asyncio.create_task(disconnect_from_all_channels())


def set_bot_instance(bot):
    """Set the bot instance for voice operations."""
    global bot_instance
    bot_instance = bot
    print("🤖 Bot instance set for voice tracking")


async def join_voice_channel(channel_id):
    """Join a voice channel to indicate active tracking."""
    global bot_instance, bot_voice_connections
    
    if not bot_instance:
        print("❌ Bot instance not set, cannot join voice channels")
        return False
    
    try:
        channel = bot_instance.get_channel(channel_id)
        if not channel:
            print(f"❌ Could not find channel {channel_id}")
            return False
        
        if not isinstance(channel, discord.VoiceChannel):
            print(f"❌ Channel {channel_id} is not a voice channel")
            return False
        
        # Check if bot is already connected to this channel
        if channel_id in bot_voice_connections:
            print(f"✅ Bot already connected to {channel.name}")
            return True
        
        # Connect to the voice channel
        voice_client = await channel.connect()
        bot_voice_connections[channel_id] = voice_client
        
        print(f"🎤 Bot joined voice channel: {channel.name}")
        return True
        
    except discord.errors.ClientException as e:
        if "already connected" in str(e):
            print("⚠️ Bot already connected to a voice channel")
            return True
        print(f"❌ Error joining voice channel {channel_id}: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error joining voice channel {channel_id}: {e}")
        return False


async def leave_voice_channel(channel_id):
    """Leave a voice channel when tracking stops."""
    global bot_voice_connections
    
    try:
        if channel_id in bot_voice_connections:
            voice_client = bot_voice_connections[channel_id]
            await voice_client.disconnect()
            del bot_voice_connections[channel_id]
            
            if bot_instance:
                channel = bot_instance.get_channel(channel_id)
                channel_name = channel.name if channel else f"Channel {channel_id}"
                print(f"🔇 Bot left voice channel: {channel_name}")
            
            return True
    except Exception as e:
        print(f"❌ Error leaving voice channel {channel_id}: {e}")
        return False


async def add_tracked_channel(channel_id, should_join=False):
    """
    Add a voice channel to participation tracking and optionally join it.
    
    Args:
        channel_id: The Discord channel ID to track
        should_join: Whether the bot should attempt to join this channel
    """
    active_voice_channels[channel_id] = datetime.now()
    last_checks[channel_id] = datetime.now()
    
    if should_join:
        # Join the voice channel to provide visual indication
        success = await join_voice_channel(channel_id)
        
        if success:
            print(f"✅ Added channel {channel_id} to voice tracking and joined")
        else:
            print(f"⚠️ Added channel {channel_id} to voice tracking (could not join)")
    else:
        print(f"✅ Added channel {channel_id} to voice tracking")
        return True


async def remove_tracked_channel(channel_id):
    """
    Remove a voice channel from participation tracking and leave it.
    
    Args:
        channel_id: The Discord channel ID to stop tracking
    """
    if channel_id in active_voice_channels:
        del active_voice_channels[channel_id]
    
    if channel_id in last_checks:
        del last_checks[channel_id]
    
    # Leave the voice channel
    await leave_voice_channel(channel_id)
    
    # Clean up member times for this channel
    # Note: This is simplified - in practice we'd need to track which channel each member is in
    print(f"✅ Removed channel {channel_id} from voice tracking and left")


def get_tracking_status():
    """
    Get current voice tracking status.
    
    Returns:
        dict: Status information about tracked channels and members
    """
    return {
        'tracked_channels': len(active_voice_channels),
        'tracked_members': len(member_times),
        'task_running': log_members.is_running(),
        'bot_connected_channels': len(bot_voice_connections),
        'voice_connections': list(bot_voice_connections.keys())
    }


async def setup(bot):
    """Setup function for discord.py extension loading."""
    global bot_instance
    bot_instance = bot
    
    # Register the voice state update handler
    @bot.event
    async def on_voice_state_update(member, before, after):
        await _handle_voice_state_update(member, before, after)
    
    # Start the logging task
    if not log_members.is_running():
        log_members.start()
    
    print("✅ Voice tracking handler loaded")
