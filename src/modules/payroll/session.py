"""
Event-Driven Payroll Session Management

Manages persistent payroll calculation sessions with event-driven state updates.
Replaces the broken modal chain system with resilient, resumable workflows.
"""

import uuid
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from decimal import Decimal
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import get_database_url
from database.connection import get_cursor

logger = logging.getLogger(__name__)

class PayrollEvent:
    """Event type constants for payroll workflow."""
    SESSION_CREATED = "session_created"
    EVENT_SELECTED = "event_selected"
    ORE_QUANTITY_UPDATED = "ore_quantity_updated"
    PRICING_LOADED = "pricing_loaded"
    STEP_COMPLETED = "step_completed"
    CALCULATION_COMPLETED = "calculation_completed"
    SESSION_EXPIRED = "session_expired"
    ERROR_OCCURRED = "error_occurred"

class PayrollStep:
    """Step constants for payroll workflow."""
    EVENT_SELECTION = "event_selection"
    ORE_SELECTION = "ore_selection" 
    QUANTITY_ENTRY = "quantity_entry"
    PRICING_REVIEW = "pricing_review"
    CALCULATION_REVIEW = "calculation_review"
    COMPLETED = "completed"

class PayrollSessionManager:
    """Manages payroll calculation sessions with event-driven architecture."""
    
    def __init__(self):
        self.db_url = get_database_url()
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.active_sessions: Dict[str, Dict] = {}
        
    def register_handler(self, event_type: str, handler: Callable):
        """Register an event handler for a specific event type."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for event: {event_type}")
    
    async def emit_event(self, event_type: str, session_id: str, event_data: Dict = None):
        """Emit an event and trigger all registered handlers."""
        if event_data is None:
            event_data = {}
            
        logger.info(f"Emitting event {event_type} for session {session_id}")
        
        # Log event to database
        await self._log_session_event(session_id, event_type, event_data)
        
        # Trigger handlers
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(session_id, event_data)
            except Exception as e:
                logger.error(f"Error in event handler {handler.__name__} for {event_type}: {e}")
                await self.emit_event(PayrollEvent.ERROR_OCCURRED, session_id, {
                    'error': str(e),
                    'handler': handler.__name__,
                    'original_event': event_type
                })
    
    async def create_session(
        self, 
        user_id: int, 
        guild_id: int, 
        event_id: str, 
        event_type: str = 'mining'
    ) -> str:
        """Create a new payroll calculation session."""
        session_id = f"payroll_{uuid.uuid4().hex[:8]}"
        
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO payroll_sessions (
                        session_id, user_id, guild_id, event_id, event_type, 
                        current_step, created_at, expires_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    session_id, user_id, guild_id, event_id, event_type,
                    PayrollStep.EVENT_SELECTION, datetime.now(), 
                    datetime.now() + timedelta(hours=2)
                ))
            
            logger.info(f"Created payroll session {session_id} for user {user_id}")
            await self.emit_event(PayrollEvent.SESSION_CREATED, session_id, {
                'user_id': user_id,
                'guild_id': guild_id,
                'event_id': event_id,
                'event_type': event_type
            })
            
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating payroll session: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data by ID."""
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM payroll_sessions WHERE session_id = %s
                """, (session_id,))
                
                row = cursor.fetchone()
                if row:
                    session_data = dict(row)
                    # Convert JSON fields
                    session_data['ore_quantities'] = session_data.get('ore_quantities') or {}
                    session_data['pricing_data'] = session_data.get('pricing_data') or {}
                    session_data['calculation_data'] = session_data.get('calculation_data') or {}
                    return session_data
                return None
                
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    async def update_session(self, session_id: str, updates: Dict):
        """Update session data."""
        try:
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                if key in ['ore_quantities', 'pricing_data', 'calculation_data']:
                    set_clauses.append(f"{key} = %s")
                    values.append(json.dumps(value, cls=PayrollJSONEncoder) if isinstance(value, dict) else value)
                elif key in ['current_step', 'donation_percentage', 'is_completed']:
                    set_clauses.append(f"{key} = %s")
                    values.append(value)
            
            if not set_clauses:
                return
                
            values.append(session_id)
            
            with get_cursor() as cursor:
                cursor.execute(f"""
                    UPDATE payroll_sessions 
                    SET {', '.join(set_clauses)}
                    WHERE session_id = %s
                """, values)
            
            logger.info(f"Updated session {session_id}: {list(updates.keys())}")
            
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            raise
    
    async def advance_step(self, session_id: str, new_step: str):
        """Advance session to next step."""
        await self.update_session(session_id, {'current_step': new_step})
        await self.emit_event(PayrollEvent.STEP_COMPLETED, session_id, {
            'new_step': new_step
        })
    
    async def update_ore_quantity(self, session_id: str, ore: str, quantity: float):
        """Update ore quantity in session."""
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return
            
        ore_quantities = session['ore_quantities'].copy()
        if quantity > 0:
            ore_quantities[ore] = quantity
        elif ore in ore_quantities:
            del ore_quantities[ore]
        
        await self.update_session(session_id, {'ore_quantities': ore_quantities})
        await self.emit_event(PayrollEvent.ORE_QUANTITY_UPDATED, session_id, {
            'ore': ore,
            'quantity': quantity,
            'total_ores': len(ore_quantities)
        })
    
    async def set_pricing_data(self, session_id: str, pricing_data: Dict):
        """Set pricing data for session."""
        await self.update_session(session_id, {'pricing_data': pricing_data})
        await self.emit_event(PayrollEvent.PRICING_LOADED, session_id, {
            'ore_count': len(pricing_data)
        })
    
    async def complete_calculation(self, session_id: str, calculation_result: Dict):
        """Mark session as completed with final calculation."""
        await self.update_session(session_id, {
            'calculation_data': calculation_result,
            'current_step': PayrollStep.COMPLETED,
            'is_completed': True
        })
        await self.emit_event(PayrollEvent.CALCULATION_COMPLETED, session_id, {
            'payroll_id': calculation_result.get('payroll_id'),
            'total_value': str(calculation_result.get('total_value_auec', 0))
        })
    
    async def get_user_active_session(self, user_id: int, guild_id: int) -> Optional[str]:
        """Get user's active session in guild."""
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT session_id FROM payroll_sessions 
                    WHERE user_id = %s AND guild_id = %s 
                    AND is_completed = FALSE AND expires_at > NOW()
                    ORDER BY created_at DESC LIMIT 1
                """, (user_id, guild_id))
                
                row = cursor.fetchone()
                return row['session_id'] if row else None
                
        except Exception as e:
            logger.error(f"Error getting active session for user {user_id}: {e}")
            return None
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        try:
            with get_cursor() as cursor:
                cursor.execute("SELECT cleanup_expired_payroll_sessions()")
                result = cursor.fetchone()
                deleted_count = result[0] if result else 0
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} expired payroll sessions")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0
    
    async def _log_session_event(self, session_id: str, event_type: str, event_data: Dict):
        """Log session event to database."""
        try:
            # Get user_id from session
            session = await self.get_session(session_id)
            if not session:
                return
                
            with get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO payroll_session_events (
                        session_id, event_type, event_data, user_id
                    ) VALUES (%s, %s, %s, %s)
                """, (
                    session_id, event_type, 
                    json.dumps(event_data, cls=PayrollJSONEncoder), session['user_id']
                ))
                
        except Exception as e:
            logger.error(f"Error logging session event: {e}")

class PayrollJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime and Decimal objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

# Global session manager instance
session_manager = PayrollSessionManager()