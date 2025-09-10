"""
Payroll Core Calculator

Universal payroll calculation engine that works across all event types.
Handles participation-based distribution, donations, and payout generation.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
import logging

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import get_database_url
from database.connection import get_cursor

logger = logging.getLogger(__name__)

class PayrollCalculator:
    """
    Universal payroll calculator for all event types.
    
    Core responsibilities:
    - Retrieve event and participation data
    - Calculate fair distribution based on participation time
    - Handle voluntary donation system
    - Generate payroll records and payouts
    - Create audit trail with price snapshots
    """
    
    def __init__(self):
        self.db_url = get_database_url()
    
    async def get_completed_events(
        self, 
        guild_id: int, 
        event_type: str, 
        limit: int = 10,
        include_calculated: bool = False
    ) -> List[Dict]:
        """Get completed events of a specific type for payroll calculation."""
        try:
            with get_cursor() as cursor:
                # Base query for completed events
                where_clause = """
                    WHERE guild_id = %s 
                    AND event_type = %s 
                    AND status = 'closed'
                """
                params = [guild_id, event_type]
                
                # Optionally exclude already calculated payrolls
                if not include_calculated:
                    where_clause += " AND (payroll_calculated = FALSE OR payroll_calculated IS NULL)"
                
                cursor.execute(f"""
                    SELECT 
                        event_id, event_name, organizer_name, 
                        started_at, ended_at, location_notes,
                        total_participants, total_duration_minutes,
                        payroll_calculated, payroll_calculated_at
                    FROM events 
                    {where_clause}
                    ORDER BY ended_at DESC
                    LIMIT %s
                """, params + [limit])
                
                events = []
                for row in cursor.fetchall():
                    event_data = dict(row)
                    
                    # Get participant count for display
                    cursor.execute("""
                        SELECT COUNT(DISTINCT user_id) as participant_count
                        FROM participation 
                        WHERE event_id = %s
                    """, (event_data['event_id'],))
                    
                    participant_result = cursor.fetchone()
                    event_data['participant_count'] = participant_result['participant_count'] if participant_result else 0
                    
                    events.append(event_data)
                
                return events
                
        except Exception as e:
            logger.error(f"Error getting completed events: {e}")
            return []
    
    async def get_event_by_id(self, event_id: str) -> Optional[Dict]:
        """Get specific event by ID."""
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM events WHERE event_id = %s
                """, (event_id,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Error getting event by ID {event_id}: {e}")
            return None
    
    async def get_event_participants(self, event_id: str) -> List[Dict]:
        """Get all participants for an event with their participation time."""
        try:
            with get_cursor() as cursor:
                # First, check if there are any participation records at all
                cursor.execute("""
                    SELECT COUNT(*) as total_records
                    FROM participation 
                    WHERE event_id = %s
                """, (event_id,))
                
                record_check = cursor.fetchone()
                logger.info(f"Found {record_check['total_records']} participation records for event {event_id}")
                
                # Get participants with their participation time
                cursor.execute("""
                    SELECT 
                        user_id, username, display_name,
                        SUM(COALESCE(duration_minutes, 0)) as total_minutes,
                        COUNT(*) as session_count,
                        MAX(is_org_member) as is_org_member,
                        MIN(joined_at) as first_joined,
                        MAX(COALESCE(left_at, joined_at)) as last_active
                    FROM participation 
                    WHERE event_id = %s
                    GROUP BY user_id, username, display_name
                    HAVING SUM(COALESCE(duration_minutes, 0)) >= 0
                    ORDER BY total_minutes DESC
                """, (event_id,))
                
                participants = [dict(row) for row in cursor.fetchall()]
                logger.info(f"Returning {len(participants)} participants for event {event_id}")
                
                return participants
                
        except Exception as e:
            logger.error(f"Error getting participants for event {event_id}: {e}")
            return []
    
    async def calculate_payroll(
        self,
        event_id: str,
        total_value_auec: Decimal,
        collection_data: Dict,
        price_data: Dict,
        calculated_by_id: int,
        calculated_by_name: str,
        donation_percentage: int = 0
    ) -> Dict:
        """
        Calculate payroll for an event.
        
        Args:
            event_id: Event to calculate payroll for
            total_value_auec: Total value of collected materials
            collection_data: What was collected (ore, components, etc.)
            price_data: Price information used for calculations
            calculated_by_id: Who is calculating the payroll
            calculated_by_name: Display name of calculator
            donation_percentage: Percentage of earnings to donate (0-100)
        
        Returns:
            Dict with payroll calculation results
        """
        try:
            # Get event data
            event_data = await self.get_event_by_id(event_id)
            if not event_data:
                return {'success': False, 'error': 'Event not found'}
            
            # Get participants
            participants = await self.get_event_participants(event_id)
            if not participants:
                return {'success': False, 'error': 'No participants found for event'}
            
            # Calculate total participation minutes
            total_minutes = sum(p['total_minutes'] for p in participants)
            if total_minutes <= 0:
                return {'success': False, 'error': 'No valid participation time found'}
            
            # Generate payroll ID
            payroll_id = self._generate_payroll_id(event_id)
            
            # Calculate individual payouts
            payouts = []
            total_donated_auec = Decimal('0')
            
            for participant in participants:
                participation_minutes = participant['total_minutes']
                participation_percentage = Decimal(participation_minutes) / Decimal(total_minutes)
                base_payout = total_value_auec * participation_percentage
                
                # Apply donation if specified
                if donation_percentage > 0:
                    donation_amount = base_payout * Decimal(donation_percentage) / Decimal('100')
                    final_payout = base_payout - donation_amount
                    total_donated_auec += donation_amount
                    is_donor = True
                else:
                    final_payout = base_payout
                    is_donor = False
                
                # Round to 2 decimal places
                base_payout = base_payout.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                final_payout = final_payout.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                payouts.append({
                    'user_id': participant['user_id'],
                    'username': participant['username'],
                    'participation_minutes': participation_minutes,
                    'participation_percentage': float(participation_percentage * 100),
                    'base_payout_auec': base_payout,
                    'final_payout_auec': final_payout,
                    'is_donor': is_donor
                })
            
            # Redistribute donated amounts
            if total_donated_auec > 0:
                non_donors = [p for p in payouts if not p['is_donor']]
                if non_donors:
                    bonus_per_person = total_donated_auec / len(non_donors)
                    bonus_per_person = bonus_per_person.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    
                    for payout in payouts:
                        if not payout['is_donor']:
                            payout['final_payout_auec'] += bonus_per_person
            
            # Store payroll in database
            success = await self._store_payroll(
                payroll_id=payroll_id,
                event_id=event_id,
                total_value_auec=total_value_auec,
                collection_data=collection_data,
                price_data=price_data,
                total_donated_auec=total_donated_auec,
                payouts=payouts,
                calculated_by_id=calculated_by_id,
                calculated_by_name=calculated_by_name
            )
            
            if not success:
                return {'success': False, 'error': 'Failed to store payroll calculation'}
            
            return {
                'success': True,
                'payroll_id': payroll_id,
                'event_data': event_data,
                'total_value_auec': total_value_auec,
                'total_participants': len(participants),
                'total_minutes': total_minutes,
                'total_donated_auec': total_donated_auec,
                'payouts': payouts,
                'calculated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating payroll for {event_id}: {e}")
            return {'success': False, 'error': f'Calculation error: {str(e)}'}
    
    async def get_recent_payrolls(self, guild_id: int, limit: int = 10) -> List[Dict]:
        """Get recently calculated payrolls for status display."""
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        p.payroll_id, p.event_id, p.total_value_auec,
                        p.calculated_by_name, p.calculated_at,
                        e.event_type, e.event_name, e.organizer_name
                    FROM payrolls p
                    JOIN events e ON p.event_id = e.event_id
                    WHERE e.guild_id = %s
                    ORDER BY p.calculated_at DESC
                    LIMIT %s
                """, (guild_id, limit))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting recent payrolls: {e}")
            return []
    
    async def _store_payroll(
        self,
        payroll_id: str,
        event_id: str,
        total_value_auec: Decimal,
        collection_data: Dict,
        price_data: Dict,
        total_donated_auec: Decimal,
        payouts: List[Dict],
        calculated_by_id: int,
        calculated_by_name: str
    ) -> bool:
        """Store payroll calculation in database."""
        try:
            with get_cursor() as cursor:
                # Insert payroll master record
                cursor.execute("""
                    INSERT INTO payrolls (
                        payroll_id, event_id, total_scu_collected, total_value_auec,
                        ore_prices_used, mining_yields, total_donated_auec,
                        calculated_by_id, calculated_by_name, calculated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    payroll_id,
                    event_id,
                    collection_data.get('total_scu', 0),
                    total_value_auec,
                    price_data,  # JSON snapshot of prices used
                    collection_data,  # JSON of what was collected
                    total_donated_auec,
                    calculated_by_id,
                    calculated_by_name,
                    datetime.now()
                ))
                
                # Insert individual payouts
                for payout in payouts:
                    cursor.execute("""
                        INSERT INTO payouts (
                            payroll_id, user_id, username, participation_minutes,
                            base_payout_auec, final_payout_auec, is_donor
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        payroll_id,
                        payout['user_id'],
                        payout['username'], 
                        payout['participation_minutes'],
                        payout['base_payout_auec'],
                        payout['final_payout_auec'],
                        payout['is_donor']
                    ))
                
                # Mark event as payroll calculated
                cursor.execute("""
                    UPDATE events 
                    SET payroll_calculated = TRUE,
                        payroll_calculated_at = %s,
                        payroll_calculated_by_id = %s,
                        total_value_auec = %s
                    WHERE event_id = %s
                """, (
                    datetime.now(),
                    calculated_by_id,
                    total_value_auec,
                    event_id
                ))
                
                logger.info(f"Stored payroll {payroll_id} for event {event_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error storing payroll: {e}")
            return False
    
    def _generate_payroll_id(self, event_id: str) -> str:
        """Generate a payroll ID based on the event ID."""
        # Convert 'sm-a7k2m9' to 'pay-sm-a7k2m9'
        return f"pay-{event_id}"