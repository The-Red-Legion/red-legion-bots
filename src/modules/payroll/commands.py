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
from .ui.views import EventSelectionView, PayrollConfirmationView
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
    
    @app_commands.command(name="mining", description="Calculate payroll for a completed mining session")
    @app_commands.describe(
        event_id="Optional: Specific mining event ID to calculate payroll for"
    )
    async def payroll_mining(
        self, 
        interaction: discord.Interaction,
        event_id: Optional[str] = None
    ):
        """Calculate payroll for mining operations."""
        await self._handle_payroll_calculation(interaction, 'mining', event_id)
    
    @app_commands.command(name="salvage", description="Calculate payroll for a completed salvage operation") 
    @app_commands.describe(
        event_id="Optional: Specific salvage event ID to calculate payroll for"
    )
    async def payroll_salvage(
        self,
        interaction: discord.Interaction,
        event_id: Optional[str] = None
    ):
        """Calculate payroll for salvage operations."""
        await self._handle_payroll_calculation(interaction, 'salvage', event_id)
    
    @app_commands.command(name="combat", description="Calculate payroll for a completed combat mission")
    @app_commands.describe(
        event_id="Optional: Specific combat event ID to calculate payroll for"
    )
    async def payroll_combat(
        self,
        interaction: discord.Interaction, 
        event_id: Optional[str] = None
    ):
        """Calculate payroll for combat operations."""
        await self._handle_payroll_calculation(interaction, 'combat', event_id)
    
    async def _handle_payroll_calculation(
        self, 
        interaction: discord.Interaction, 
        event_type: str,
        event_id: Optional[str] = None
    ):
        """Universal payroll calculation handler for all event types."""
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
            
            guild_id = interaction.guild_id
            processor = self.processors[event_type]
            
            # If specific event_id provided, use it directly
            if event_id:
                event_data = await self.calculator.get_event_by_id(event_id)
                if not event_data:
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title="❌ Event Not Found",
                            description=f"Event `{event_id}` not found or not accessible.",
                            color=discord.Color.red()
                        ),
                        ephemeral=True
                    )
                    return
                    
                if event_data['event_type'] != event_type:
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title="❌ Wrong Event Type",
                            description=f"Event `{event_id}` is a {event_data['event_type']} event, not {event_type}.",
                            color=discord.Color.red()
                        ),
                        ephemeral=True
                    )
                    return
                
                # Skip event selection, go straight to collection input
                await self._show_collection_modal(interaction, event_data, processor)
                return
            
            # Get available completed events for this type
            events = await self.calculator.get_completed_events(guild_id, event_type)
            
            if not events:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title=f"ℹ️ No {event_type.title()} Events Found",
                        description=f"No completed {event_type} events found that need payroll calculation.\n\n"
                                  f"**To create {event_type} events:**\n"
                                  f"• Use `/{event_type} start` to begin a session\n"
                                  f"• Use `/{event_type} stop` to end the session\n"
                                  f"• Then return here to calculate payroll",
                        color=discord.Color.blue()
                    ),
                    ephemeral=True
                )
                return
            
            # Show event selection view
            embed = discord.Embed(
                title=f"💰 {event_type.title()} Payroll Calculator",
                description=f"Select a completed {event_type} event to calculate payroll for:",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📋 Available Events",
                value=f"Found **{len(events)}** completed {event_type} events awaiting payroll calculation.",
                inline=False
            )
            
            embed.add_field(
                name="🔄 Process",
                value=f"1. Select event from dropdown\n"
                      f"2. Enter {processor.get_collection_description()}\n"
                      f"3. Review and confirm payroll calculation\n"
                      f"4. Generate final payout summary",
                inline=False
            )
            
            view = EventSelectionView(events, event_type, processor, self.calculator)
            
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
                
                # Show pending event IDs (up to 8 events to avoid embed limits)
                if all_pending_events:
                    event_list = []
                    for event in all_pending_events[:8]:
                        event_emoji = {'mining': '⛏️', 'salvage': '🔧', 'combat': '⚔️'}.get(event['type'], '📋')
                        event_list.append(f"{event_emoji} `{event['event_id']}`")
                    
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