"""
Payroll UI Views

Discord views for event selection, payroll confirmation, and result display.
"""

import discord
from discord import ui
from typing import Dict, List
from decimal import Decimal
from datetime import datetime


class EventSelectionView(ui.View):
    """View for selecting which event to calculate payroll for."""
    
    def __init__(self, events: List[Dict], event_type: str, processor, calculator):
        super().__init__(timeout=300)
        self.events = events
        self.event_type = event_type
        self.processor = processor
        self.calculator = calculator
        
        # Create dropdown with events
        self.add_item(EventSelectionDropdown(events, event_type, processor, calculator))


class EventSelectionDropdown(ui.Select):
    """Dropdown for selecting an event."""
    
    def __init__(self, events: List[Dict], event_type: str, processor, calculator):
        self.events = events
        self.event_type = event_type
        self.processor = processor
        self.calculator = calculator
        
        # Create options for dropdown
        options = []
        for event in events[:25]:  # Discord limit
            # Format event display
            duration = event.get('total_duration_minutes', 0)
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
            
            # Build description with participants, duration, and location
            description = f"{start_date} • {event.get('total_participants', 0)} participants • {duration_text}"
            if event.get('location_notes'):
                # Truncate location to fit in description limit
                location_short = event['location_notes'][:20] + "..." if len(event['location_notes']) > 20 else event['location_notes']
                description += f" • {location_short}"
            
            options.append(discord.SelectOption(
                label=f"{event['event_id']} - {event['organizer_name']}",
                description=description[:100],  # Discord limit
                value=event['event_id']
            ))
        
        super().__init__(
            placeholder=f"Choose a {event_type} event to calculate payroll for...",
            options=options,
            min_values=1,
            max_values=1
        )
    
    async def callback(self, interaction: discord.Interaction):
        selected_event_id = self.values[0]
        
        # Find selected event
        selected_event = None
        for event in self.events:
            if event['event_id'] == selected_event_id:
                selected_event = event
                break
        
        if not selected_event:
            await interaction.response.send_message("❌ Event not found", ephemeral=True)
            return
        
        # Show appropriate collection modal
        from .modals import MiningCollectionModal, SalvageCollectionModal
        
        if self.event_type == 'mining':
            modal = MiningCollectionModal(selected_event, self.processor, self.calculator)
        elif self.event_type == 'salvage':
            modal = SalvageCollectionModal(selected_event, self.processor, self.calculator)
        else:
            # Default to mining modal for now
            modal = MiningCollectionModal(selected_event, self.processor, self.calculator)
        
        await interaction.response.send_modal(modal)


class PayrollConfirmationView(ui.View):
    """View for confirming payroll calculation with donation options."""
    
    def __init__(
        self, 
        event_data: Dict,
        ore_collections: Dict,
        prices: Dict,
        total_value: Decimal,
        breakdown: Dict,
        processor,
        calculator
    ):
        super().__init__(timeout=600)
        
        self.event_data = event_data
        self.ore_collections = ore_collections
        self.prices = prices
        self.total_value = total_value
        self.breakdown = breakdown
        self.processor = processor
        self.calculator = calculator
        
        # Add donation percentage selector
        self.add_item(DonationSelector())
        
        # Add confirm button
        self.add_item(ConfirmPayrollButton(
            event_data, ore_collections, prices, total_value, 
            breakdown, processor, calculator
        ))
        
        # Add cancel button
        self.add_item(CancelButton())


class DonationSelector(ui.Select):
    """Dropdown for selecting donation percentage."""
    
    def __init__(self):
        options = [
            discord.SelectOption(
                label="No Donations (100% payout)",
                description="Everyone keeps their full earnings",
                value="0",
                emoji="💰"
            ),
            discord.SelectOption(
                label="10% Donation",
                description="10% donated, redistributed to non-donors",
                value="10",
                emoji="🤝"
            ),
            discord.SelectOption(
                label="15% Donation", 
                description="15% donated, redistributed to non-donors",
                value="15",
                emoji="💝"
            ),
            discord.SelectOption(
                label="20% Donation",
                description="20% donated, redistributed to non-donors", 
                value="20",
                emoji="🎁"
            )
        ]
        
        super().__init__(
            placeholder="Select donation percentage (optional)",
            options=options,
            min_values=1,
            max_values=1
        )
        
        self.donation_percentage = 0
    
    async def callback(self, interaction: discord.Interaction):
        self.donation_percentage = int(self.values[0])
        
        if self.donation_percentage > 0:
            await interaction.response.send_message(
                f"✅ Set donation percentage to {self.donation_percentage}%\n"
                f"Members who donate will have {self.donation_percentage}% redistributed to non-donors.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "✅ No donations - everyone keeps their full earnings.",
                ephemeral=True
            )


class ConfirmPayrollButton(ui.Button):
    """Button to confirm and execute payroll calculation."""
    
    def __init__(
        self, 
        event_data: Dict,
        ore_collections: Dict, 
        prices: Dict,
        total_value: Decimal,
        breakdown: Dict,
        processor,
        calculator
    ):
        super().__init__(
            label="Calculate Payroll",
            style=discord.ButtonStyle.success,
            emoji="✅"
        )
        
        self.event_data = event_data
        self.ore_collections = ore_collections
        self.prices = prices
        self.total_value = total_value
        self.breakdown = breakdown
        self.processor = processor
        self.calculator = calculator
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Get donation percentage from selector
        donation_percentage = 0
        for item in self.view.children:
            if isinstance(item, DonationSelector):
                donation_percentage = item.donation_percentage
                break
        
        try:
            # Calculate payroll
            result = await self.calculator.calculate_payroll(
                event_id=self.event_data['event_id'],
                total_value_auec=self.total_value,
                collection_data={
                    'ores': self.ore_collections,
                    'total_scu': sum(self.ore_collections.values()),
                    'breakdown': self.breakdown
                },
                price_data=self.prices,
                calculated_by_id=interaction.user.id,
                calculated_by_name=interaction.user.display_name,
                donation_percentage=donation_percentage
            )
            
            if not result['success']:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ Payroll Calculation Failed",
                        description=result['error'],
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return
            
            # Show final payroll results
            await self._show_payroll_results(interaction, result)
            
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error Calculating Payroll",
                    description=f"An unexpected error occurred: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
    
    async def _show_payroll_results(self, interaction: discord.Interaction, result: Dict):
        """Display final payroll calculation results."""
        embed = discord.Embed(
            title="✅ Payroll Calculation Complete",
            description=f"**Event:** {result['event_data']['event_id']}\n"
                       f"**Total Value:** {result['total_value_auec']:,.2f} aUEC\n"
                       f"**Participants:** {result['total_participants']}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        # Summary stats
        embed.add_field(
            name="📊 Distribution Summary",
            value=f"**Session Duration:** {result['total_minutes']} minutes\n"
                  f"**Total Donated:** {result['total_donated_auec']:,.2f} aUEC\n"
                  f"**Payroll ID:** `{result['payroll_id']}`",
            inline=False
        )
        
        # Show top payouts
        top_payouts = sorted(result['payouts'], key=lambda x: x['final_payout_auec'], reverse=True)[:5]
        payout_text = []
        for payout in top_payouts:
            donation_marker = " 🎁" if payout['is_donor'] else ""
            payout_text.append(
                f"**{payout['username']}:** {payout['final_payout_auec']:,.0f} aUEC "
                f"({payout['participation_minutes']}min){donation_marker}"
            )
        
        embed.add_field(
            name="🏆 Top Payouts",
            value="\n".join(payout_text),
            inline=False
        )
        
        if len(result['payouts']) > 5:
            embed.add_field(
                name="📋 Full Report",
                value=f"See complete payout details for all {len(result['payouts'])} participants.",
                inline=False
            )
        
        embed.set_footer(text=f"Calculated by {result['payouts'][0]['username'] if result['payouts'] else 'System'}")
        
        # Disable all buttons in the view
        for item in self.view.children:
            item.disabled = True
        
        await interaction.edit_original_response(embed=embed, view=self.view)


class CancelButton(ui.Button):
    """Button to cancel payroll calculation."""
    
    def __init__(self):
        super().__init__(
            label="Cancel",
            style=discord.ButtonStyle.secondary,
            emoji="❌"
        )
    
    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="❌ Payroll Calculation Cancelled",
            description="The payroll calculation has been cancelled.",
            color=discord.Color.orange()
        )
        
        # Disable all buttons
        for item in self.view.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self.view)