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

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .core import PayrollCalculator
from .processors import MiningProcessor, SalvageProcessor, CombatProcessor
from .ui.views import EventSelectionView, PayrollConfirmationView, UnifiedEventSelectionView
from .ui.modals import MiningCollectionModal, SalvageCollectionModal

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
        interaction: discord.Interaction,
        event_id: Optional[str] = None
    ):
        """Unified payroll calculation for all event types."""
        await self._handle_unified_payroll_calculation(interaction, event_id)
    
    async def _handle_unified_payroll_calculation(
        self,
        interaction: discord.Interaction,
        event_id: Optional[str] = None
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
            
            # If specific event_id provided, handle directly (no defer needed for modals)
            if event_id:
                event_data = await self.calculator.get_event_by_id(event_id)
                if not event_data:
                    await interaction.response.send_message(
                        embed=discord.Embed(
                            title="❌ Event Not Found",
                            description=f"Event `{event_id}` not found or not accessible.",
                            color=discord.Color.red()
                        ),
                        ephemeral=True
                    )
                    return
                
                # Get processor for this event type
                event_type = event_data.get('event_type', 'mining')
                processor = self.processors.get(event_type, self.processors['mining'])
                
                # Skip event selection, go straight to collection input
                await self._show_collection_modal(interaction, event_data, processor)
                return
            
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
            
            view = UnifiedEventSelectionView(all_events, self.processors, self.calculator)
            
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
    
    # DEPRECATED: Old individual payroll commands - kept for backwards compatibility
    # Use /payroll calculate instead
    
    @app_commands.command(name="mining", description="[DEPRECATED] Calculate payroll for mining - use /payroll calculate instead")
    @app_commands.describe(event_id="Event ID to calculate payroll for")
    async def payroll_mining_deprecated(self, interaction: discord.Interaction, event_id: Optional[str] = None):
        """Deprecated mining payroll command - redirects to unified command."""
        await interaction.response.send_message(
            embed=discord.Embed(
                title="⚠️ Command Deprecated",
                description="This command has been replaced with `/payroll calculate` for a better experience.\n\n"
                          "**New unified payroll:**\n"
                          "• Use `/payroll calculate` to see all event types\n"
                          "• Choose from mining, salvage, or combat events\n"
                          "• Better UI with dates and participant counts",
                color=discord.Color.orange()
            ),
            ephemeral=True
        )
    
    @app_commands.command(name="salvage", description="[DEPRECATED] Calculate payroll for salvage - use /payroll calculate instead")
    @app_commands.describe(event_id="Event ID to calculate payroll for")
    async def payroll_salvage_deprecated(self, interaction: discord.Interaction, event_id: Optional[str] = None):
        """Deprecated salvage payroll command - redirects to unified command."""
        await interaction.response.send_message(
            embed=discord.Embed(
                title="⚠️ Command Deprecated",
                description="This command has been replaced with `/payroll calculate` for a better experience.\n\n"
                          "**New unified payroll:**\n"
                          "• Use `/payroll calculate` to see all event types\n"
                          "• Choose from mining, salvage, or combat events\n"
                          "• Better UI with dates and participant counts",
                color=discord.Color.orange()
            ),
            ephemeral=True
        )
    
    @app_commands.command(name="combat", description="[DEPRECATED] Calculate payroll for combat - use /payroll calculate instead")
    @app_commands.describe(event_id="Event ID to calculate payroll for")
    async def payroll_combat_deprecated(self, interaction: discord.Interaction, event_id: Optional[str] = None):
        """Deprecated combat payroll command - redirects to unified command."""
        await interaction.response.send_message(
            embed=discord.Embed(
                title="⚠️ Command Deprecated",
                description="This command has been replaced with `/payroll calculate` for a better experience.\n\n"
                          "**New unified payroll:**\n"
                          "• Use `/payroll calculate` to see all event types\n"
                          "• Choose from mining, salvage, or combat events\n"
                          "• Better UI with dates and participant counts",
                color=discord.Color.orange()
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
                        'ended_at': event.get('ended_at', 'N/A')
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