"""
Payroll Commands for Red Legion Bot

Universal payroll system supporting all event types:
- /payroll mining - Calculate mining session payroll
- /payroll salvage - Calculate salvage operation payroll
- /payroll combat - Calculate combat mission payroll

Uses the unified database schema with event-centric design.
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Optional, List, Dict
import sys
from pathlib import Path
import logging

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

from .core import PayrollCalculator
from .processors import MiningProcessor, SalvageProcessor, CombatProcessor
from .ui.views import EventSelectionView, PayrollConfirmationView, UnifiedEventSelectionView
from .ui.modals import MiningCollectionModal, SalvageCollectionModal
from .ui.event_selection_v2 import EventDrivenEventSelectionView
from .session import session_manager

class PayrollCommands(commands.GroupCog, name="payroll", description="Calculate payouts for mining, salvage, and combat operations"):
    """Universal payroll command group."""
    
    def __init__(self, bot):
        self.bot = bot
        self.calculator = PayrollCalculator()
        
        # Processors for different event types
        self.processors = {
            'mining': MiningProcessor(),
            'salvage': SalvageProcessor(),
            'combat': CombatProcessor()
        }
        super().__init__()
    
    @app_commands.command(name="calculate", description="Calculate payroll - shows selection menu for all event types (mining, salvage, combat)")
    async def payroll_calculate(
        self, 
        interaction: discord.Interaction
    ):
        """Unified payroll calculation for all event types."""
        # Check for existing active session first
        existing_session_id = await session_manager.get_user_active_session(
            interaction.user.id, interaction.guild_id
        )
        
        if existing_session_id:
            await self._handle_resume_session(interaction, existing_session_id)
        else:
            await self._handle_unified_payroll_calculation(interaction)
    
    @app_commands.command(name="resume", description="Resume your active payroll calculation session")
    async def payroll_resume(
        self,
        interaction: discord.Interaction
    ):
        """Resume an active payroll session."""
        existing_session_id = await session_manager.get_user_active_session(
            interaction.user.id, interaction.guild_id
        )
        
        if existing_session_id:
            await self._handle_resume_session(interaction, existing_session_id)
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="ℹ️ No Active Session",
                    description="You don't have any active payroll calculation sessions.\n"
                               "Use `/payroll calculate` to start a new calculation.",
                    color=discord.Color.blue()
                ),
                ephemeral=True
            )
    
    @app_commands.command(name="quick", description="Quick mining payroll calculation with ore quantities as parameters")
    @app_commands.describe(
        event_id="Mining event ID (e.g., sm-abc123)",
        quantanium="Quantanium SCU amount (default: 0)",
        laranite="Laranite SCU amount (default: 0)", 
        agricium="Agricium SCU amount (default: 0)",
        hadanite="Hadanite SCU amount (default: 0)",
        beryl="Beryl SCU amount (default: 0)",
        donation="Donation percentage: 0, 5, 10, 15, or 20 (default: 10)"
    )
    async def payroll_quick(
        self,
        interaction: discord.Interaction,
        event_id: str,
        quantanium: float = 0.0,
        laranite: float = 0.0,
        agricium: float = 0.0, 
        hadanite: float = 0.0,
        beryl: float = 0.0,
        donation: float = 10.0
    ):
        """Quick mining payroll calculation without modals."""
        await interaction.response.defer()
        
        try:
            # Check permissions
            if not await self._check_payroll_permissions(interaction.user):
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ Permission Denied",
                        description="You need payroll management permissions to use this command.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return
            
            # Validate donation percentage
            if int(donation) not in [0, 5, 10, 15, 20]:
                await interaction.followup.send(
                    "❌ Donation percentage must be 0, 5, 10, 15, or 20.",
                    ephemeral=True
                )
                return
            
            donation = int(donation)  # Convert to int for calculations
            
            # Check if event exists
            guild_id = interaction.guild_id
            events = await self.calculator.get_completed_events(guild_id, 'mining', include_calculated=False)
            target_event = None
            
            for event in events:
                if event['event_id'] == event_id:
                    target_event = event
                    break
            
            if not target_event:
                await interaction.followup.send(
                    f"❌ Event `{event_id}` not found or already has payroll calculated.",
                    ephemeral=True
                )
                return
            
            # Build ore quantities dict
            ore_quantities = {}
            ores = {
                'QUAN': quantanium,
                'LARA': laranite, 
                'AGRI': agricium,
                'HADA': hadanite,
                'BERY': beryl
            }
            
            total_scu = 0
            for ore_code, amount in ores.items():
                if amount > 0:
                    ore_quantities[ore_code] = amount
                    total_scu += amount
            
            if total_scu == 0:
                await interaction.followup.send(
                    "❌ Please specify at least some ore quantities greater than 0.",
                    ephemeral=True
                )
                return
            
            # Get prices and calculate
            await interaction.followup.send("🔄 Fetching current UEX Corp ore prices...", ephemeral=True)
            
            ore_prices = await self.processors['mining'].get_current_prices()
            if not ore_prices:
                # Use fallback prices
                ore_prices = {
                    'QUAN': {'price': 9000}, 'LARA': {'price': 2500}, 'AGRI': {'price': 2300},
                    'HADA': {'price': 1800}, 'BERY': {'price': 1600}
                }
                await interaction.followup.send("⚠️ Using fallback prices (UEX API unavailable)", ephemeral=True)
            
            # Calculate total value
            total_value, breakdown = await self.processors['mining'].calculate_total_value(
                ore_quantities, ore_prices
            )
            
            # Get participants
            participants = await self.calculator.get_participants_for_event(event_id)
            if not participants:
                await interaction.followup.send(
                    f"❌ No participants found for event {event_id}.",
                    ephemeral=True
                )
                return
            
            # Calculate final amounts
            donation_amount = total_value * (donation / 100)
            payout_amount = total_value - donation_amount
            per_participant = payout_amount / len(participants) if len(participants) > 0 else 0
            
            # Create final payroll summary
            embed = discord.Embed(
                title=f"💰 Quick Payroll - {event_id}",
                description=f"**Payroll calculation complete!**",
                color=discord.Color.green()
            )
            
            # Add ore breakdown
            ore_text = []
            for ore_code, quantity in ore_quantities.items():
                if ore_code in breakdown:
                    data = breakdown[ore_code]
                    ore_name = {'QUAN': 'Quantanium', 'LARA': 'Laranite', 'AGRI': 'Agricium', 'HADA': 'Hadanite', 'BERY': 'Beryl'}.get(ore_code, ore_code)
                    ore_text.append(f"• **{ore_name}:** {quantity} SCU @ {data['price_per_scu']:,.0f} = {data['total_value']:,.0f} aUEC")
            
            embed.add_field(
                name="⛏️ Ore Collections",
                value="\n".join(ore_text),
                inline=False
            )
            
            embed.add_field(
                name="💰 Financial Summary",
                value=f"**Total Value:** {total_value:,.0f} aUEC\n"
                      f"**Donation ({donation}%):** {donation_amount:,.0f} aUEC\n"
                      f"**Net Payout:** {payout_amount:,.0f} aUEC",
                inline=False
            )
            
            embed.add_field(
                name="👥 Distribution",
                value=f"**{len(participants)} participants** receive equal shares\n"
                      f"**Per participant:** {per_participant:,.0f} aUEC\n"
                      f"**Payment method:** Manual distribution",
                inline=False
            )
            
            # Add participant list (first few)
            participant_text = []
            for participant in participants[:5]:
                participant_text.append(f"• {participant.get('display_name', 'Unknown')}")
            if len(participants) > 5:
                participant_text.append(f"... and {len(participants) - 5} more")
            
            embed.add_field(
                name="📋 Participants",
                value="\n".join(participant_text),
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error calculating payroll: {str(e)}",
                ephemeral=True
            )
    
    async def _handle_resume_session(
        self,
        interaction: discord.Interaction,
        session_id: str
    ):
        """Resume an existing payroll session."""
        try:
            await interaction.response.defer()
            
            session = await session_manager.get_session(session_id)
            if not session:
                await interaction.followup.send(
                    "❌ Session not found or expired.", ephemeral=True
                )
                return
            
            current_step = session['current_step']
            event_type = session['event_type']
            processor = self.processors[event_type]
            
            if current_step == 'quantity_entry':
                # Resume ore quantity entry
                from .ui.views_v2 import OreQuantityEntryView
                view = OreQuantityEntryView(session_id, processor)
                embed, quantity_view = await view.build_current_view()
                
                await interaction.edit_original_response(embed=embed, view=quantity_view)
                
            elif current_step == 'pricing_review':
                # Resume pricing review
                from .ui.views_v2 import PricingReviewView
                view = PricingReviewView(session_id)
                embed, pricing_view = await view.build_current_view()
                
                await interaction.edit_original_response(embed=embed, view=pricing_view)
                
            elif current_step == 'payout_management':
                # Resume payout management
                from .ui.views_v2 import PayoutManagementView
                view = PayoutManagementView(session_id)
                embed = await view.create_embed()
                
                await interaction.edit_original_response(embed=embed, view=view)
                
            else:
                # Fallback to event selection
                await self._handle_unified_payroll_calculation(interaction)
                
        except Exception as e:
            logger.error(f"Error resuming session {session_id}: {e}")
            await interaction.followup.send(
                f"❌ Error resuming session: {str(e)}", ephemeral=True
            )
    
    async def _handle_unified_payroll_calculation(
        self,
        interaction: discord.Interaction
    ):
        """Unified handler for payroll calculation across all event types."""
        try:
            # Check permissions first (before any response)
            if not await self._check_payroll_permissions(interaction.user):
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ Permission Denied",
                        description="You need payroll management permissions to use this command.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return
            
            guild_id = interaction.guild_id
            
            # For dropdown selection, we need to defer since we're doing database queries
            await interaction.response.defer()
            
            # Get all pending events across all types
            all_events = {}
            total_pending = 0
            
            for event_type in ['mining', 'salvage', 'combat']:
                events = await self.calculator.get_completed_events(guild_id, event_type, include_calculated=False)
                all_events[event_type] = events
                total_pending += len(events)
            
            if total_pending == 0:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="ℹ️ No Events Found",
                        description="No completed events found that need payroll calculation.\n\n"
                                  "**To create events:**\n"
                                  "• Use `/mining start` to begin a mining session\n"
                                  "• Use event commands for salvage and combat operations\n"
                                  "• Then return here to calculate payroll",
                        color=discord.Color.blue()
                    ),
                    ephemeral=True
                )
                return
            
            # Show unified event selection view
            embed = discord.Embed(
                title="💰 Universal Payroll Calculator",
                description="Select any completed event to calculate payroll for:",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            # Add breakdown by event type
            breakdown_lines = []
            for event_type, events in all_events.items():
                if len(events) > 0:
                    emoji = {'mining': '⛏️', 'salvage': '🔧', 'combat': '⚔️'}.get(event_type, '📋')
                    breakdown_lines.append(f"{emoji} **{event_type.title()}:** {len(events)} events")
            
            embed.add_field(
                name="📋 Available Events",
                value="\n".join(breakdown_lines) + f"\n\n**Total:** {total_pending} events awaiting payroll",
                inline=False
            )
            
            embed.add_field(
                name="🔄 Process",
                value="1. Select any event from dropdown (shows type, date & participants)\n"
                      "2. Enter collection data specific to that event type\n"
                      "3. Review and confirm payroll calculation\n"
                      "4. Generate final payout summary",
                inline=False
            )
            
            # Add cleanup of expired sessions
            await session_manager.cleanup_expired_sessions()
            
            view = EventDrivenEventSelectionView(all_events, self.processors)
            
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error Calculating Payroll",
                    description=f"An unexpected error occurred: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
    
    async def _show_collection_modal(
        self, 
        interaction: discord.Interaction,
        event_data: Dict,
        processor
    ):
        """Show the appropriate collection input modal for the event type."""
        event_type = event_data['event_type']
        
        if event_type == 'mining':
            modal = MiningCollectionModal(event_data, processor, self.calculator)
        elif event_type == 'salvage':
            modal = SalvageCollectionModal(event_data, processor, self.calculator)
        else:
            # For combat and other types, use a generic collection modal
            modal = MiningCollectionModal(event_data, processor, self.calculator)  # Temporary
        
        await interaction.response.send_modal(modal)
    
    async def _check_payroll_permissions(self, user: discord.Member) -> bool:
        """Check if user has permissions to manage payroll."""
        # Check if user has permissions to manage payroll
        return (
            user.guild_permissions.administrator or 
            any(role.name.lower() in ['admin', 'orgleader', 'payroll', 'officer'] for role in user.roles)
        )
    
    @app_commands.command(name="status", description="Show payroll calculation status and recent activity")
    async def payroll_status(self, interaction: discord.Interaction):
        """Show payroll system status and recent calculations."""
        await interaction.response.defer()
        
        try:
            guild_id = interaction.guild_id
            
            # Get recent payroll calculations
            recent_payrolls = await self.calculator.get_recent_payrolls(guild_id, limit=5)
            
            # Get pending events by type with details
            pending_stats = {}
            all_pending_events = []
            for event_type in ['mining', 'salvage', 'combat']:
                events = await self.calculator.get_completed_events(guild_id, event_type, include_calculated=False)
                pending_stats[event_type] = len(events)
                # Store events with their details for display
                for event in events:
                    all_pending_events.append({
                        'event_id': event['event_id'], 
                        'type': event_type,
                        'started_at': event.get('started_at'),
                        'ended_at': event.get('ended_at', 'N/A'),
                        'location_notes': event.get('location_notes')
                    })
            
            embed = discord.Embed(
                title="💰 Payroll System Status",
                description="Current payroll calculation status and recent activity",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            # Pending calculations summary
            pending_total = sum(pending_stats.values())
            if pending_total > 0:
                pending_text = []
                for event_type, count in pending_stats.items():
                    if count > 0:
                        pending_text.append(f"**{event_type.title()}:** {count} events")
                
                embed.add_field(
                    name="⏳ Pending Calculations",
                    value="\n".join(pending_text) if pending_text else "None",
                    inline=True
                )
                
                # Show pending event IDs with start dates (up to 8 events to avoid embed limits)
                if all_pending_events:
                    event_list = []
                    for event in all_pending_events[:8]:
                        event_emoji = {'mining': '⛏️', 'salvage': '🔧', 'combat': '⚔️'}.get(event['type'], '📋')
                        
                        # Format start date
                        if event['started_at']:
                            # Convert to timestamp for Discord formatting
                            if isinstance(event['started_at'], str):
                                started_at = datetime.fromisoformat(event['started_at'].replace('Z', '+00:00'))
                            else:
                                started_at = event['started_at']
                            start_date = f"<t:{int(started_at.timestamp())}:d>"
                        else:
                            start_date = "Unknown"
                        
                        # Add location if available
                        location_info = ""
                        if event.get('location_notes'):
                            location_short = event['location_notes'][:20] + "..." if len(event['location_notes']) > 20 else event['location_notes']
                            location_info = f" @ {location_short}"
                        
                        event_list.append(f"{event_emoji} `{event['event_id']}` - {start_date}{location_info}")
                    
                    if len(all_pending_events) > 8:
                        event_list.append(f"... and {len(all_pending_events) - 8} more")
                    
                    embed.add_field(
                        name="📋 Pending Event IDs",
                        value="\n".join(event_list),
                        inline=False
                    )
            else:
                embed.add_field(
                    name="✅ All Caught Up",
                    value="No pending payroll calculations",
                    inline=True
                )
            
            # Recent activity
            if recent_payrolls:
                recent_text = []
                for payroll in recent_payrolls[:3]:
                    event_type = payroll['event_id'].split('-')[0]
                    event_type_name = {'sm': 'Mining', 'sv': 'Salvage', 'op': 'Combat'}.get(event_type, 'Unknown')
                    calc_date = payroll['calculated_at'].strftime("%m/%d")
                    recent_text.append(f"• {event_type_name} `{payroll['event_id']}` - {calc_date}")
                
                embed.add_field(
                    name="📊 Recent Calculations",
                    value="\n".join(recent_text),
                    inline=True
                )
            
            # Quick actions
            embed.add_field(
                name="🚀 Quick Actions",
                value="• `/payroll mining` - Calculate mining payroll\n"
                      "• `/payroll salvage` - Calculate salvage payroll\n"
                      "• `/payroll combat` - Calculate combat payroll",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error Getting Payroll Status",
                    description=f"An unexpected error occurred: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )


async def setup(bot):
    """Setup function for discord.py extension loading.""" 
    await bot.add_cog(PayrollCommands(bot))