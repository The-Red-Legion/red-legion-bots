"""
Voice Participation Tracking for Mining Events

Tracks member participation in voice channels during mining sessions.
Integrates with the unified database schema using the 'participation' table.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging
import discord

# Add src to path for imports  
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import get_database_url
from database.connection import get_cursor

logger = logging.getLogger(__name__)

class VoiceTracker:
    """
    Manages voice channel participation tracking for mining events.
    
    Stores participation data in the unified 'participation' table with:
    - event_id: Links to events table
    - user_id, username, display_name: Participant info
    - channel_id, channel_name: Which voice channel
    - joined_at, left_at: Time tracking for payroll
    - is_org_member: Critical for lottery eligibility
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.db_url = get_database_url()
        self.tracked_events = {}  # {event_id: {channel_ids, participants}}
    
    async def start_tracking(self, event_id: str, channels: Dict[str, str]) -> Dict:
        """
        Start voice tracking for a mining event.
        
        Args:
            event_id: Mining event ID (e.g., 'sm-a7k2m9')
            channels: Dict of {channel_name: channel_id}
        
        Returns:
            Dict with 'success' and 'error' keys
        """
        try:
            # Convert channel IDs to integers
            channel_ids = []
            for name, channel_id in channels.items():
                try:
                    channel_ids.append(int(channel_id))
                except ValueError:
                    logger.warning(f"Invalid channel ID for {name}: {channel_id}")
            
            if not channel_ids:
                return {
                    'success': False,
                    'error': 'No valid voice channels found for tracking'
                }
            
            # Store tracking info
            self.tracked_events[event_id] = {
                'channel_ids': set(channel_ids),
                'channels': channels,
                'participants': {}  # {user_id: participation_data}
            }
            
            # Check for members already in voice channels
            await self._check_existing_participants(event_id)
            
            logger.info(f"Started voice tracking for event {event_id} with {len(channel_ids)} channels")
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error starting voice tracking for {event_id}: {e}")
            return {
                'success': False,
                'error': f'Failed to start voice tracking: {str(e)}'
            }
    
    async def stop_tracking(self, event_id: str):
        """Stop voice tracking for an event and finalize all participation records."""
        try:
            if event_id not in self.tracked_events:
                logger.warning(f"Attempted to stop tracking for unknown event: {event_id}")
                return
            
            tracking_data = self.tracked_events[event_id]
            
            # Finalize all active participants
            for user_id, participant in tracking_data['participants'].items():
                if not participant.get('left_at'):
                    await self._record_participant_leave(event_id, user_id)
            
            # Remove from tracking
            del self.tracked_events[event_id]
            
            logger.info(f"Stopped voice tracking for event {event_id}")
            
        except Exception as e:
            logger.error(f"Error stopping voice tracking for {event_id}: {e}")
    
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Handle voice state changes for tracked events."""
        try:
            # Check each tracked event to see if this affects them
            for event_id, tracking_data in self.tracked_events.items():
                channel_ids = tracking_data['channel_ids']
                
                # Member left a tracked channel
                if before.channel and before.channel.id in channel_ids:
                    await self._record_participant_leave(event_id, member.id)
                
                # Member joined a tracked channel  
                if after.channel and after.channel.id in channel_ids:
                    await self._record_participant_join(event_id, member, after.channel)
                    
        except Exception as e:
            logger.error(f"Error handling voice state update: {e}")
    
    async def get_current_participants(self, event_id: str) -> List[Dict]:
        """Get currently active participants for an event."""
        try:
            if event_id not in self.tracked_events:
                return []
            
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT user_id, username, display_name, channel_name, joined_at
                    FROM participation 
                    WHERE event_id = %s 
                    AND left_at IS NULL
                    ORDER BY joined_at
                """, (event_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting current participants for {event_id}: {e}")
            return []
    
    async def _check_existing_participants(self, event_id: str):
        """Check for members already in voice channels when tracking starts."""
        try:
            tracking_data = self.tracked_events[event_id]
            channel_ids = tracking_data['channel_ids']
            
            # Get all guilds the bot is in
            for guild in self.bot.guilds:
                for channel_id in channel_ids:
                    channel = guild.get_channel(channel_id)
                    if channel and isinstance(channel, discord.VoiceChannel):
                        # Record all current members as joining
                        for member in channel.members:
                            if not member.bot:  # Skip bots
                                await self._record_participant_join(event_id, member, channel)
                                
        except Exception as e:
            logger.error(f"Error checking existing participants: {e}")
    
    async def _record_participant_join(self, event_id: str, member: discord.Member, channel: discord.VoiceChannel):
        """Record a participant joining a voice channel."""
        try:
            # Check if already active in this event
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT id FROM participation 
                    WHERE event_id = %s AND user_id = %s AND left_at IS NULL
                """, (event_id, member.id))
                
                if cursor.fetchone():
                    logger.debug(f"Member {member.display_name} already active in event {event_id}")
                    return
                
                # Check org member status
                is_org_member = await self._check_org_member_status(member)
                
                # Insert participation record
                cursor.execute("""
                    INSERT INTO participation (
                        event_id, user_id, username, display_name,
                        channel_id, channel_name, joined_at, is_org_member
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    event_id,
                    member.id,
                    member.name,
                    member.display_name,
                    channel.id,
                    channel.name,
                    datetime.now(),
                    is_org_member
                ))
                
                # Update tracking data
                tracking_data = self.tracked_events[event_id]
                tracking_data['participants'][member.id] = {
                    'joined_at': datetime.now(),
                    'channel_name': channel.name,
                    'left_at': None
                }
                
                logger.info(f"Recorded {member.display_name} joining {channel.name} for event {event_id}")
                
        except Exception as e:
            logger.error(f"Error recording participant join: {e}")
    
    async def _record_participant_leave(self, event_id: str, user_id: int):
        """Record a participant leaving a voice channel.""" 
        try:
            leave_time = datetime.now()
            
            with get_cursor() as cursor:
                # Update the most recent participation record
                cursor.execute("""
                    UPDATE participation 
                    SET left_at = %s,
                        duration_minutes = EXTRACT(EPOCH FROM (%s - joined_at))/60,
                        updated_at = %s
                    WHERE event_id = %s 
                    AND user_id = %s 
                    AND left_at IS NULL
                    RETURNING username
                """, (leave_time, leave_time, leave_time, event_id, user_id))
                
                result = cursor.fetchone()
                
                if result:
                    # Update tracking data
                    if event_id in self.tracked_events:
                        tracking_data = self.tracked_events[event_id]
                        if user_id in tracking_data['participants']:
                            tracking_data['participants'][user_id]['left_at'] = leave_time
                    
                    logger.info(f"Recorded {result['username']} leaving voice channel for event {event_id}")
                    
        except Exception as e:
            logger.error(f"Error recording participant leave: {e}")
    
    async def _check_org_member_status(self, member: discord.Member) -> bool:
        """Check if a member has org member role for lottery eligibility."""
        try:
            from config.settings import DISCORD_CONFIG
            org_role_id = DISCORD_CONFIG.get('ORG_ROLE_ID')
            
            if not org_role_id:
                return False
            
            # Check if member has the org role
            org_role = member.guild.get_role(int(org_role_id))
            return org_role in member.roles if org_role else False
            
        except Exception as e:
            logger.error(f"Error checking org member status for {member.display_name}: {e}")
            return False