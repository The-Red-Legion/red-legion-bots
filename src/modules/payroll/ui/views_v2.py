"""
Event-Driven View-Based Payroll UI

Replaces modal chains with resilient view-based interface using session management.
Provides smooth, non-blocking user experience with real-time updates.
"""

import discord
from discord import ui
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ..session import session_manager, PayrollEvent, PayrollStep
from ..processors.mining import MiningProcessor
from ..core import PayrollCalculator

logger = logging.getLogger(__name__)

class EventDrivenPayrollView(ui.View):
    """Base class for event-driven payroll views."""
    
    def __init__(self, session_id: str, timeout: int = 600):
        super().__init__(timeout=timeout)
        self.session_id = session_id
        self.session_data = None
        
    async def load_session(self):
        """Load current session data."""
        self.session_data = await session_manager.get_session(self.session_id)
        return self.session_data
    
    async def refresh_view(self, interaction: discord.Interaction):
        """Refresh the view with current session data."""
        await self.load_session()
        embed, view = await self.build_current_view()
        
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed, view=view)
        else:
            await interaction.response.edit_message(embed=embed, view=view)
    
    async def build_current_view(self):
        """Build the current view based on session state. Override in subclasses."""
        raise NotImplementedError

class OreQuantityEntryView(EventDrivenPayrollView):
    """View-based ore quantity entry with real-time updates."""
    
    def __init__(self, session_id: str, processor: MiningProcessor):
        super().__init__(session_id)
        self.processor = processor
        self.ore_names = {
            'QUAN': 'Quantanium', 'LARA': 'Laranite', 'AGRI': 'Agricium', 
            'BEXA': 'Bexalite', 'GOLD': 'Gold', 'BERY': 'Beryl', 
            'HADA': 'Hadanite', 'HEPH': 'Hephaestanite', 'BORA': 'Borase',
            'TUNG': 'Tungsten', 'TITA': 'Titanium', 'ALUM': 'Aluminum',
            'COPP': 'Copper', 'DIAM': 'Diamond', 'TARA': 'Taranite'
        }
        self.current_prices = {}
        
    async def build_current_view(self):
        """Build ore quantity entry interface."""
        await self.load_session()
        
        if not self.session_data:
            embed = discord.Embed(
                title="❌ Session Error", 
                description="Session not found", 
                color=discord.Color.red()
            )
            return embed, None
        
        # Get current prices (database only)
        self.current_prices = await self.processor.get_current_prices(
            refresh=False, allow_api_calls=False
        )
        
        # Build main embed
        embed = discord.Embed(
            title=f"⛏️ Mining Payroll - {self.session_data['event_id']}",
            description="**Step 2 of 4: Enter Ore Quantities** 📊\n\n"
                       "Enter the SCU amounts for each ore type collected.",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # Current quantities and totals
        ore_quantities = self.session_data.get('ore_quantities', {})
        total_value = Decimal('0')
        total_scu = 0
        
        quantity_lines = []
        for ore_code, ore_name in sorted(self.ore_names.items(), key=lambda x: x[1]):
            quantity = ore_quantities.get(ore_code, 0)
            price_info = self.current_prices.get(ore_code, {'price': 0})
            price_per_scu = Decimal(str(price_info['price']))
            ore_value = Decimal(str(quantity)) * price_per_scu
            total_value += ore_value
            total_scu += quantity
            
            if quantity > 0:
                quantity_lines.append(
                    f"**{ore_name}:** {quantity:,.0f} SCU @ {price_per_scu:,.0f} = {ore_value:,.0f} aUEC"
                )
            else:
                quantity_lines.append(f"{ore_name}: *Not collected*")
        
        embed.add_field(
            name="📊 Current Quantities",
            value="\n".join(quantity_lines[:8]),  # First 8 ores
            inline=False
        )
        
        if len(quantity_lines) > 8:
            embed.add_field(
                name="📊 More Ores",
                value="\n".join(quantity_lines[8:]),
                inline=False
            )
        
        embed.add_field(
            name="💰 Summary",
            value=f"**Total SCU:** {total_scu:,.0f}\n"
                  f"**Total Value:** {total_value:,.0f} aUEC\n"
                  f"**Ores with Quantities:** {len([q for q in ore_quantities.values() if q > 0])}",
            inline=False
        )
        
        # Build view with ore buttons
        view = OreQuantityEntryView(self.session_id, self.processor)
        await view._build_ore_buttons()
        
        return embed, view
    
    async def _build_ore_buttons(self):
        """Build ore quantity entry buttons."""
        await self.load_session()
        ore_quantities = self.session_data.get('ore_quantities', {})
        
        # Create rows of ore buttons (5 per row max)
        ore_items = list(self.ore_names.items())
        
        for i in range(0, len(ore_items), 5):
            row_ores = ore_items[i:i+5]
            for ore_code, ore_name in row_ores:
                quantity = ore_quantities.get(ore_code, 0)
                button_label = f"{ore_name}: {quantity:,.0f}" if quantity > 0 else ore_name
                button_style = discord.ButtonStyle.primary if quantity > 0 else discord.ButtonStyle.secondary
                
                button = OreQuantityButton(ore_code, ore_name, self.session_id)
                button.label = button_label[:80]  # Discord limit
                button.style = button_style
                self.add_item(button)
        
        # Add navigation buttons
        continue_button = ContinueToPricingButton(self.session_id)
        continue_button.disabled = len([q for q in ore_quantities.values() if q > 0]) == 0
        self.add_item(continue_button)
        
        self.add_item(CancelSessionButton(self.session_id))

class OreQuantityButton(ui.Button):
    """Button to set quantity for a specific ore."""
    
    def __init__(self, ore_code: str, ore_name: str, session_id: str):
        super().__init__(emoji="📊")
        self.ore_code = ore_code
        self.ore_name = ore_name
        self.session_id = session_id
    
    async def callback(self, interaction: discord.Interaction):
        # Show mini-modal for this specific ore
        modal = SingleOreQuantityModal(self.ore_code, self.ore_name, self.session_id)
        await interaction.response.send_modal(modal)

class SingleOreQuantityModal(ui.Modal):
    """Mini-modal for entering quantity for a single ore."""
    
    def __init__(self, ore_code: str, ore_name: str, session_id: str):
        super().__init__(title=f"Set {ore_name} Quantity")
        self.ore_code = ore_code
        self.ore_name = ore_name
        self.session_id = session_id
        
        self.quantity_input = ui.TextInput(
            label=f"{ore_name} SCU Amount",
            placeholder="Enter SCU quantity (0 to remove)",
            required=True,
            max_length=10,
            default="0"
        )
        self.add_item(self.quantity_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Parse quantity
            quantity_str = self.quantity_input.value.strip()
            quantity = float(quantity_str) if quantity_str else 0
            
            if quantity < 0:
                await interaction.response.send_message(
                    f"❌ Quantity must be 0 or greater.", ephemeral=True
                )
                return
            
            # Update session via event system
            await session_manager.update_ore_quantity(self.session_id, self.ore_code, quantity)
            
            # Refresh the main view
            session = await session_manager.get_session(self.session_id)
            if session:
                processor = MiningProcessor()
                view = OreQuantityEntryView(self.session_id, processor)
                embed, new_view = await view.build_current_view()
                
                await interaction.response.edit_message(embed=embed, view=new_view)
            else:
                await interaction.response.send_message(
                    "❌ Session not found", ephemeral=True
                )
                
        except ValueError:
            await interaction.response.send_message(
                f"❌ Invalid quantity: '{self.quantity_input.value}'", ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error in ore quantity modal: {e}")
            await interaction.response.send_message(
                f"❌ Error updating quantity: {str(e)}", ephemeral=True
            )

class ContinueToPricingButton(ui.Button):
    """Button to continue to pricing review."""
    
    def __init__(self, session_id: str):
        super().__init__(
            label="Continue to Pricing Review",
            style=discord.ButtonStyle.success,
            emoji="💰"
        )
        self.session_id = session_id
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            # Advance to pricing review step
            await session_manager.advance_step(self.session_id, PayrollStep.PRICING_REVIEW)
            
            # Show pricing review view
            view = PricingReviewView(self.session_id)
            embed, pricing_view = await view.build_current_view()
            
            await interaction.edit_original_response(embed=embed, view=pricing_view)
            
        except Exception as e:
            logger.error(f"Error advancing to pricing review: {e}")
            await interaction.followup.send(
                f"❌ Error advancing to pricing review: {str(e)}", ephemeral=True
            )

class PricingReviewView(EventDrivenPayrollView):
    """View for reviewing and confirming ore pricing."""
    
    def __init__(self, session_id: str):
        super().__init__(session_id)
        self.processor = MiningProcessor()
        self.calculator = PayrollCalculator()
    
    async def build_current_view(self):
        """Build pricing review interface."""
        await self.load_session()
        
        if not self.session_data:
            embed = discord.Embed(title="❌ Session Error", color=discord.Color.red())
            return embed, None
        
        ore_quantities = self.session_data.get('ore_quantities', {})
        if not ore_quantities:
            embed = discord.Embed(
                title="❌ No Quantities", 
                description="Please go back and enter ore quantities first.",
                color=discord.Color.red()
            )
            return embed, None
        
        # Get current pricing
        prices = await self.processor.get_current_prices(refresh=False, allow_api_calls=False)
        total_value, breakdown = await self.processor.calculate_total_value(ore_quantities, prices)
        
        # Update session with pricing data
        await session_manager.set_pricing_data(self.session_id, {
            'prices': prices,
            'breakdown': breakdown,
            'total_value': str(total_value)
        })
        
        # Build embed
        embed = discord.Embed(
            title=f"⛏️ Mining Payroll - {self.session_data['event_id']}",
            description="**Step 3 of 4: Review Pricing** 💰\n\n"
                       "Review ore prices and total value calculation.",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        # Ore breakdown
        breakdown_lines = []
        for ore_code, quantity in ore_quantities.items():
            if quantity > 0 and ore_code in breakdown:
                data = breakdown[ore_code]
                ore_name = self._get_ore_name(ore_code)
                breakdown_lines.append(
                    f"**{ore_name}:** {quantity:,.0f} SCU × {data['price_per_scu']:,.0f} = {data['total_value']:,.0f} aUEC"
                )
        
        embed.add_field(
            name="📊 Ore Value Breakdown",
            value="\n".join(breakdown_lines) if breakdown_lines else "No ores with quantities",
            inline=False
        )
        
        embed.add_field(
            name="💰 Total Value",
            value=f"**{total_value:,.0f} aUEC**",
            inline=True
        )
        
        # Build view
        view = PricingReviewView(self.session_id)
        await view._build_review_buttons()
        
        return embed, view
    
    async def _build_review_buttons(self):
        """Build pricing review buttons."""
        self.add_item(CalculatePayrollButton(self.session_id))
        self.add_item(BackToQuantitiesButton(self.session_id))
        self.add_item(CancelSessionButton(self.session_id))
    
    def _get_ore_name(self, ore_code: str) -> str:
        """Get display name for ore code."""
        ore_names = {
            'QUAN': 'Quantanium', 'LARA': 'Laranite', 'AGRI': 'Agricium',
            'BEXA': 'Bexalite', 'GOLD': 'Gold', 'BERY': 'Beryl',
            'HADA': 'Hadanite', 'HEPH': 'Hephaestanite', 'BORA': 'Borase',
            'TUNG': 'Tungsten', 'TITA': 'Titanium', 'ALUM': 'Aluminum',
            'COPP': 'Copper', 'DIAM': 'Diamond', 'TARA': 'Taranite'
        }
        return ore_names.get(ore_code, ore_code)

class CalculatePayrollButton(ui.Button):
    """Button to calculate final payroll."""
    
    def __init__(self, session_id: str):
        super().__init__(
            label="Calculate Payroll",
            style=discord.ButtonStyle.success,
            emoji="🧮"
        )
        self.session_id = session_id
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            session = await session_manager.get_session(self.session_id)
            if not session:
                await interaction.followup.send("❌ Session not found", ephemeral=True)
                return
            
            # Get pricing data
            pricing_data = session.get('pricing_data', {})
            if not pricing_data:
                await interaction.followup.send("❌ No pricing data available", ephemeral=True)
                return
            
            # Calculate payroll
            calculator = PayrollCalculator()
            result = await calculator.calculate_payroll(
                event_id=session['event_id'],
                total_value_auec=Decimal(pricing_data['total_value']),
                collection_data={
                    'ores': session['ore_quantities'],
                    'total_scu': sum(session['ore_quantities'].values()),
                    'breakdown': pricing_data['breakdown']
                },
                price_data=pricing_data['prices'],
                calculated_by_id=session['user_id'],
                calculated_by_name="Payroll Calculator",
                donation_percentage=session.get('donation_percentage', 0)
            )
            
            if result['success']:
                # Complete session
                await session_manager.complete_calculation(self.session_id, result)
                
                # Show final results
                embed = discord.Embed(
                    title="✅ Payroll Calculation Complete!",
                    description=f"**Event:** {result['event_data']['event_id']}\n"
                              f"**Total Value:** {result['total_value_auec']:,.0f} aUEC\n"
                              f"**Participants:** {result['total_participants']}",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="📊 Summary",
                    value=f"**Payroll ID:** `{result['payroll_id']}`\n"
                          f"**Session Duration:** {result['total_minutes']} minutes\n"
                          f"**Total Donated:** {result['total_donated_auec']:,.0f} aUEC",
                    inline=False
                )
                
                await interaction.edit_original_response(embed=embed, view=None)
            else:
                await interaction.followup.send(
                    f"❌ Payroll calculation failed: {result['error']}", ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Error calculating payroll: {e}")
            await interaction.followup.send(
                f"❌ Error calculating payroll: {str(e)}", ephemeral=True
            )

class BackToQuantitiesButton(ui.Button):
    """Button to go back to quantity entry."""
    
    def __init__(self, session_id: str):
        super().__init__(
            label="Back to Quantities",
            style=discord.ButtonStyle.secondary,
            emoji="⬅️"
        )
        self.session_id = session_id
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Go back to quantity entry
        await session_manager.advance_step(self.session_id, PayrollStep.QUANTITY_ENTRY)
        
        processor = MiningProcessor()
        view = OreQuantityEntryView(self.session_id, processor)
        embed, quantity_view = await view.build_current_view()
        
        await interaction.edit_original_response(embed=embed, view=quantity_view)

class CancelSessionButton(ui.Button):
    """Button to cancel the session."""
    
    def __init__(self, session_id: str):
        super().__init__(
            label="Cancel",
            style=discord.ButtonStyle.danger,
            emoji="❌"
        )
        self.session_id = session_id
    
    async def callback(self, interaction: discord.Interaction):
        # Mark session as completed (cancelled)
        await session_manager.update_session(self.session_id, {'is_completed': True})
        
        embed = discord.Embed(
            title="❌ Payroll Calculation Cancelled",
            description="The payroll calculation has been cancelled.",
            color=discord.Color.orange()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)