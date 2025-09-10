"""
Mining Event Manager

Handles mining event lifecycle using the unified database schema.
All events are stored in the central 'events' table with event_type='mining'.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import get_database_url
from database.connection import get_cursor

logger = logging.getLogger(__name__)

class MiningEventManager:
    """
    Manages mining events using the unified database schema.
    
    Events are stored in the 'events' table with:
    - event_id: Prefixed ID like 'sm-a7k2m9' 
    - event_type: 'mining'
    - status: 'open' or 'closed'
    """
    
    def __init__(self):
        self.db_url = get_database_url()
    
    async def create_event(
        self,
        guild_id: int,
        organizer_id: int,
        organizer_name: str,
        location: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Create a new mining event in the unified schema.
        
        Returns:
            Dict with 'success', 'event' (if successful), 'error' (if failed)
        """
        try:
            # Generate prefixed event ID
            event_id = self._generate_mining_event_id()
            
            # Parse location into system/planet components if provided
            system_location = None
            planet_moon = None
            location_notes = location
            
            if location:
                # Simple parsing - can be enhanced later
                location_parts = location.split(',')
                if len(location_parts) >= 2:
                    system_location = location_parts[0].strip()
                    planet_moon = location_parts[1].strip()
                    if len(location_parts) > 2:
                        location_notes = ','.join(location_parts[2:]).strip()
                elif 'stanton' in location.lower() or 'pyro' in location.lower():
                    system_location = location
                else:
                    planet_moon = location
            
            with get_cursor() as cursor:
                # Insert into unified events table
                cursor.execute("""
                    INSERT INTO events (
                        event_id, guild_id, event_type, event_name,
                        organizer_id, organizer_name, started_at, status,
                        system_location, planet_moon, location_notes, description
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) RETURNING *
                """, (
                    event_id,
                    guild_id,
                    'mining',
                    'Mining Session',
                    organizer_id, 
                    organizer_name,
                    datetime.now(),
                    'open',
                    system_location,
                    planet_moon,
                    location_notes,
                    notes
                ))
                
                event_row = cursor.fetchone()
                
                if not event_row:
                    return {
                        'success': False,
                        'error': 'Failed to create mining event in database'
                    }
                
                # Convert to dict for easier handling
                event_data = dict(event_row)
                
                logger.info(f"Created mining event {event_id} for guild {guild_id}")
                
                return {
                    'success': True,
                    'event': event_data
                }
                
        except Exception as e:
            logger.error(f"Error creating mining event: {e}")
            return {
                'success': False,
                'error': f'Database error: {str(e)}'
            }
    
    async def get_active_event(self, guild_id: int) -> Optional[Dict]:
        """Get the currently active mining event for a guild."""
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM events 
                    WHERE guild_id = %s 
                    AND event_type = 'mining' 
                    AND status = 'open'
                    ORDER BY started_at DESC
                    LIMIT 1
                """, (guild_id,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Error getting active mining event: {e}")
            return None
    
    async def close_event(
        self, 
        event_id: str, 
        closed_by_id: int, 
        closed_by_name: str
    ) -> Dict:
        """Close a mining event and calculate final stats."""
        try:
            with get_cursor() as cursor:
                # Update event status and end time
                cursor.execute("""
                    UPDATE events 
                    SET status = 'closed',
                        ended_at = %s,
                        updated_at = %s
                    WHERE event_id = %s 
                    AND status = 'open'
                    RETURNING *
                """, (datetime.now(), datetime.now(), event_id))
                
                updated_event = cursor.fetchone()
                
                if not updated_event:
                    return {
                        'success': False,
                        'error': 'Event not found or already closed'
                    }
                
                # Calculate final participation metrics
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) as total_participants
                    FROM participation 
                    WHERE event_id = %s
                """, (event_id,))
                
                participation_stats = cursor.fetchone()
                total_participants = participation_stats['total_participants'] if participation_stats else 0
                
                # Calculate event duration based on actual start/end times
                cursor.execute("""
                    SELECT started_at, ended_at
                    FROM events
                    WHERE event_id = %s
                """, (event_id,))
                
                event_times = cursor.fetchone()
                total_duration_minutes = 0
                
                if event_times and event_times['started_at'] and event_times['ended_at']:
                    duration_seconds = (event_times['ended_at'] - event_times['started_at']).total_seconds()
                    total_duration_minutes = int(duration_seconds / 60)
                
                # Update the event with final stats
                cursor.execute("""
                    UPDATE events 
                    SET total_participants = %s,
                        total_duration_minutes = %s
                    WHERE event_id = %s
                """, (
                    total_participants,
                    total_duration_minutes,
                    event_id
                ))
                
                logger.info(f"Closed mining event {event_id} by {closed_by_name}")
                
                return {
                    'success': True,
                    'event': dict(updated_event)
                }
                
        except Exception as e:
            logger.error(f"Error closing mining event {event_id}: {e}")
            return {
                'success': False,
                'error': f'Database error: {str(e)}'
            }
    
    async def get_event_stats(self, event_id: str) -> Dict:
        """Get current statistics for a mining event."""
        try:
            with get_cursor() as cursor:
                # Get basic event info
                cursor.execute("""
                    SELECT started_at, ended_at, total_participants, total_duration_minutes
                    FROM events 
                    WHERE event_id = %s
                """, (event_id,))
                
                event_data = cursor.fetchone()
                if not event_data:
                    return {}
                
                # Calculate current stats from participation table
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT user_id) as current_participants,
                        COUNT(DISTINCT CASE WHEN left_at IS NULL THEN user_id END) as active_participants,
                        COALESCE(MAX(
                            SELECT COUNT(*)
                            FROM participation p2 
                            WHERE p2.event_id = %s 
                            AND p2.joined_at <= p1.joined_at 
                            AND (p2.left_at IS NULL OR p2.left_at >= p1.joined_at)
                        ), 0) as max_concurrent
                    FROM participation p1
                    WHERE p1.event_id = %s
                """, (event_id, event_id))
                
                participation_stats = cursor.fetchone()
                
                # Calculate duration
                start_time = event_data['started_at']
                end_time = event_data['ended_at'] or datetime.now()
                duration_minutes = int((end_time - start_time).total_seconds() / 60)
                
                return {
                    'total_participants': participation_stats['current_participants'] or 0,
                    'active_participants': participation_stats['active_participants'] or 0, 
                    'max_concurrent': participation_stats['max_concurrent'] or 0,
                    'duration_minutes': duration_minutes,
                    'started_at': start_time.isoformat(),
                    'ended_at': end_time.isoformat() if event_data['ended_at'] else None
                }
                
        except Exception as e:
            logger.error(f"Error getting stats for event {event_id}: {e}")
            return {}
    
    async def get_completed_events(self, guild_id: int, limit: int = 10) -> List[Dict]:
        """Get recently completed mining events for payroll processing."""
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT event_id, event_name, organizer_name, started_at, ended_at,
                           total_participants, total_duration_minutes, location_notes,
                           payroll_calculated
                    FROM events 
                    WHERE guild_id = %s 
                    AND event_type = 'mining' 
                    AND status = 'closed'
                    ORDER BY ended_at DESC
                    LIMIT %s
                """, (guild_id, limit))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting completed mining events: {e}")
            return []
    
    async def fix_event_durations(self, guild_id: int = None) -> Dict:
        """Fix duration calculations for events that have zero duration but should have duration."""
        try:
            fixed_count = 0
            with get_cursor() as cursor:
                # Find events with zero duration but valid start/end times
                where_clause = "WHERE ended_at IS NOT NULL AND started_at IS NOT NULL AND (total_duration_minutes = 0 OR total_duration_minutes IS NULL)"
                params = []
                
                if guild_id:
                    where_clause += " AND guild_id = %s"
                    params.append(guild_id)
                
                cursor.execute(f"""
                    SELECT event_id, started_at, ended_at
                    FROM events 
                    {where_clause}
                """, params)
                
                events_to_fix = cursor.fetchall()
                
                for event in events_to_fix:
                    # Calculate correct duration
                    duration_seconds = (event['ended_at'] - event['started_at']).total_seconds()
                    duration_minutes = int(duration_seconds / 60)
                    
                    # Update the event
                    cursor.execute("""
                        UPDATE events 
                        SET total_duration_minutes = %s
                        WHERE event_id = %s
                    """, (duration_minutes, event['event_id']))
                    
                    if cursor.rowcount > 0:
                        fixed_count += 1
                        logger.info(f"Fixed duration for event {event['event_id']}: {duration_minutes} minutes")
                
                return {
                    'success': True,
                    'fixed_count': fixed_count,
                    'message': f"Fixed duration for {fixed_count} events"
                }
                
        except Exception as e:
            logger.error(f"Error fixing event durations: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_mining_event_id(self) -> str:
        """Generate a prefixed mining event ID like 'sm-a7k2m9'."""
        import random
        
        # Generate 6 character alphanumeric string to match database constraint
        chars = '0123456789abcdefghijklmnopqrstuvwxyz'
        random_part = ''.join(random.choices(chars, k=6))
        
        return f"sm-{random_part}"