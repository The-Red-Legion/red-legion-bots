"""
Event-Driven Event Selection for Payroll

Integrates with the new session management system to provide seamless event selection
that leads into the view-based ore quantity entry system.
"""

import discord
from discord import ui
from typing import Dict, List
from datetime import datetime
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ..session import session_manager, PayrollStep
from ..processors.mining import MiningProcessor
from .views_v2 import OreQuantityEntryView

logger = logging.getLogger(__name__)

def format_event_date(date_value) -> str:
    """Format event date to year-month-day hour:minute."""
    if not date_value:
        return "Unknown"
    
    try:
        if isinstance(date_value, str):
            parsed_date = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
        else:
            parsed_date = date_value
        return parsed_date.strftime("%Y-%m-%d %H:%M")
    except:
        return "Unknown"

class EventDrivenEventSelectionView(ui.View):
    """Event selection view that integrates with session management."""
    
    def __init__(self, all_events: Dict[str, List[Dict]], processors: Dict):
        super().__init__(timeout=300)
        self.all_events = all_events
        self.processors = processors
        
        # Add the event selection dropdown
        self.add_item(EventDrivenEventDropdown(all_events, processors))

class EventDrivenEventDropdown(ui.Select):
    """Event selection dropdown that creates sessions and launches view-based UI."""
    
    def __init__(self, all_events: Dict[str, List[Dict]], processors: Dict):
        self.all_events = all_events
        self.processors = processors
        
        # Create options for dropdown from all event types
        options = []
        event_emojis = {'mining': '⛏️', 'salvage': '🔧', 'combat': '⚔️'}
        
        # Combine all events and sort by start date (newest first)
        combined_events = []
        for event_type, events in all_events.items():
            for event in events:
                event['event_type'] = event_type
                combined_events.append(event)
        
        # Sort by start date (newest first)
        combined_events.sort(key=lambda x: x.get('started_at', ''), reverse=True)
        
        for event in combined_events[:25]:  # Discord limit
            event_type = event['event_type']
            event_emoji = event_emojis.get(event_type, '📋')
            
            # Format event display  
            duration = event.get('total_duration_minutes', 0) or 0
            duration_text = f"{duration // 60}h {duration % 60}m" if duration > 60 else f"{duration}m"
            
            # Format start date for display
            start_date = "Unknown Date"
            if event.get('started_at'):
                try:
                    if isinstance(event['started_at'], str):
                        started_at = datetime.fromisoformat(event['started_at'].replace('Z', '+00:00'))
                    else:
                        started_at = event['started_at']
                    start_date = started_at.strftime("%m/%d %H:%M")
                except:
                    start_date = "Unknown Date"
            
            # Build description with type, date, participants, duration, and location
            participant_count = event.get('participant_count', event.get('total_participants', 0))
            description = f"{event_type.title()} • {start_date} • {participant_count} participants • {duration_text}"
            if event.get('location_notes'):
                # Truncate location to fit in description limit
                location_short = event['location_notes'][:15] + "..." if len(event['location_notes']) > 15 else event['location_notes']
                description += f" • {location_short}"
            
            options.append(discord.SelectOption(
                label=f"{event_emoji} {event['event_id']} - {event['organizer_name']}",
                description=description[:100],  # Discord limit
                value=f"{event_type}:{event['event_id']}"  # Include type for processing
            ))
        
        super().__init__(
            placeholder="Choose any event to calculate payroll for...",
            options=options,
            min_values=1,
            max_values=1
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            selected_value = self.values[0]
            event_type, event_id = selected_value.split(':', 1)
            
            # Find selected event
            selected_event = None
            for event in self.all_events[event_type]:
                if event['event_id'] == event_id:
                    selected_event = event
                    selected_event['event_type'] = event_type  # Ensure type is set
                    break
            
            if not selected_event:
                await interaction.followup.send("❌ Event not found", ephemeral=True)
                return
            
            # Check if user has an existing active session
            existing_session_id = await session_manager.get_user_active_session(
                interaction.user.id, interaction.guild_id
            )
            
            if existing_session_id:
                # Resume existing session or create new one
                await session_manager.update_session(existing_session_id, {'is_completed': True})
                logger.info(f"Closed existing session {existing_session_id} for user {interaction.user.id}")
            
            # Create new payroll session
            session_id = await session_manager.create_session(
                user_id=interaction.user.id,
                guild_id=interaction.guild_id,
                event_id=event_id,
                event_type=event_type
            )
            
            # Advance to quantity entry step
            await session_manager.advance_step(session_id, PayrollStep.QUANTITY_ENTRY)
            
            # Get the appropriate processor
            processor = self.processors[event_type]
            
            # Show appropriate interface based on event type
            if event_type == 'mining':
                # Launch view-based ore quantity entry
                view = OreQuantityEntryView(session_id, processor)
                embed, quantity_view = await view.build_current_view()
                
                await interaction.edit_original_response(embed=embed, view=quantity_view)
                
            elif event_type == 'salvage':
                # For now, use the same system but indicate it's salvage
                view = OreQuantityEntryView(session_id, processor)
                embed, quantity_view = await view.build_current_view()
                
                # Update embed title for salvage
                embed.title = f"🔧 Salvage Payroll - {selected_event['event_id']}"
                embed.description = "**Step 2 of 4: Enter Material Quantities** 📊\n\n" \
                                   "Enter the quantities for materials collected during salvage."
                
                await interaction.edit_original_response(embed=embed, view=quantity_view)
                
            else:
                # Combat and other types - use mining system as placeholder
                view = OreQuantityEntryView(session_id, processor)
                embed, quantity_view = await view.build_current_view()
                
                # Update embed for combat
                embed.title = f"⚔️ Combat Payroll - {selected_event['event_id']}"
                embed.description = "**Step 2 of 4: Enter Material Quantities** 📊\n\n" \
                                   "Enter quantities for materials collected during combat operations."
                
                await interaction.edit_original_response(embed=embed, view=quantity_view)
            
            logger.info(f"Started payroll session {session_id} for event {event_id} (type: {event_type})")
            
        except Exception as e:
            logger.error(f"Error in event selection: {e}")
            await interaction.followup.send(
                f"❌ Error starting payroll session: {str(e)}", ephemeral=True
            )