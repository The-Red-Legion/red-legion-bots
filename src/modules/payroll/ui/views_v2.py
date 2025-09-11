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
        # Use full ore names to match pricing system (alphabetical order)
        self.ore_names = {
            'AGRICIUM': 'Agricium', 'ALUMINUM': 'Aluminum', 'BERYL': 'Beryl', 
            'BEXALITE': 'Bexalite', 'BORASE': 'Borase', 'COPPER': 'Copper',
            'CORUNDUM': 'Corundum', 'DIAMOND': 'Diamond', 'GOLD': 'Gold',
            'HADANITE': 'Hadanite', 'HEPHAESTANITE': 'Hephaestanite', 'IRON': 'Iron',
            'LARANITE': 'Laranite', 'QUANTAINIUM': 'Quantanium', 'QUARTZ': 'Quartz',
            'RICCITE': 'Riccite', 'SILICON': 'Silicon', 'STILERON': 'Stileron',
            'TARANITE': 'Taranite', 'TITANIUM': 'Titanium', 'TUNGSTEN': 'Tungsten'
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
                    f"**{ore_name}:** {quantity:,.0f} SCU @ {price_per_scu:,.1f} = {ore_value:,.0f} aUEC"
                )
            else:
                quantity_lines.append(f"{ore_name}: *Not collected*")
        
        # Consolidate all ores under one title, split into multiple fields if needed due to Discord limits
        all_quantities_text = "\n".join(quantity_lines)
        if len(all_quantities_text) <= 1024:
            # All ores fit in one field
            embed.add_field(
                name="📊 Current Quantities",
                value=all_quantities_text,
                inline=False
            )
        else:
            # Split into multiple fields but keep same title
            embed.add_field(
                name="📊 Current Quantities",
                value="\n".join(quantity_lines[:8]),
                inline=False
            )
            
            if len(quantity_lines) > 8:
                embed.add_field(
                    name="📊 Current Quantities (cont.)",
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
        continue_button = ContinueToCustomPricingButton(self.session_id)
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

class ContinueToCustomPricingButton(ui.Button):
    """Button to continue to custom pricing step."""
    
    def __init__(self, session_id: str):
        super().__init__(
            label="Review/Set Pricing",
            style=discord.ButtonStyle.success,
            emoji="💰"
        )
        self.session_id = session_id
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            # Advance to custom pricing step
            await session_manager.advance_step(self.session_id, PayrollStep.CUSTOM_PRICING)
            
            # Show custom pricing view
            view = CustomPricingView(self.session_id)
            embed = await view.create_embed()
            
            await interaction.edit_original_response(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error advancing to custom pricing: {e}")
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
        
        # Get current pricing - allow API calls during pricing review step as it's not during immediate Discord interaction
        prices = await self.processor.get_current_prices(refresh=True, allow_api_calls=True)
        
        # Apply custom pricing overrides if they exist
        custom_prices = self.session_data.get('custom_prices', {})
        if custom_prices:
            # Create reverse lookup to match display names to ore codes
            ore_name_to_code = {
                'Agricium': 'AGRICIUM', 'Aluminum': 'ALUMINUM', 'Beryl': 'BERYL',
                'Bexalite': 'BEXALITE', 'Borase': 'BORASE', 'Copper': 'COPPER',
                'Corundum': 'CORUNDUM', 'Diamond': 'DIAMOND', 'Gold': 'GOLD',
                'Hadanite': 'HADANITE', 'Hephaestanite': 'HEPHAESTANITE', 'Iron': 'IRON',
                'Laranite': 'LARANITE', 'Quantanium': 'QUANTAINIUM', 'Quartz': 'QUARTZ',
                'Riccite': 'RICCITE', 'Silicon': 'SILICON', 'Stileron': 'STILERON',
                'Taranite': 'TARANITE', 'Titanium': 'TITANIUM', 'Tungsten': 'TUNGSTEN'
            }
            
            for ore_display_name, custom_price in custom_prices.items():
                ore_code = ore_name_to_code.get(ore_display_name, ore_display_name.upper())
                if ore_code in prices:
                    prices[ore_code]['price'] = custom_price
        
        total_value, breakdown = await self.processor.calculate_total_value(ore_quantities, prices)
        
        # Update session with pricing data
        await session_manager.set_pricing_data(self.session_id, {
            'prices': prices,
            'breakdown': breakdown,
            'total_value': str(total_value)
        })
        
        # Build embed with enhanced formatting
        embed = discord.Embed(
            title=f"# ⛏️ Mining Payroll - {self.session_data['event_id']}",
            description="## **Step 3 of 4: Review Pricing** 💰\n\n"
                       "📋 **Review ore prices and total value calculation**\n"
                       "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        # Ore breakdown with better spacing
        breakdown_lines = []
        for ore_code, quantity in ore_quantities.items():
            if quantity > 0 and ore_code in breakdown:
                data = breakdown[ore_code]
                ore_name = self._get_ore_name(ore_code)
                breakdown_lines.append(
                    f"```\n{ore_name:12} │ {quantity:>8,.0f} SCU  ×  {data['price_per_scu']:>6,.0f}  =  {data['total_value']:>12,.0f} aUEC```"
                )
        
        embed.add_field(
            name="📊 Ore Value Breakdown",
            value="\n".join(breakdown_lines) if breakdown_lines else "No ores with quantities",
            inline=False
        )
        
        embed.add_field(
            name="💰 **TOTAL VALUE**",
            value=f"```ansi\n[1;32m{total_value:>15,.0f} aUEC[0m```",
            inline=False
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
            'AGRICIUM': 'Agricium', 'ALUMINUM': 'Aluminum', 'BERYL': 'Beryl',
            'BEXALITE': 'Bexalite', 'BORASE': 'Borase', 'COPPER': 'Copper',
            'CORUNDUM': 'Corundum', 'DIAMOND': 'Diamond', 'GOLD': 'Gold',
            'HADANITE': 'Hadanite', 'HEPHAESTANITE': 'Hephaestanite', 'IRON': 'Iron',
            'LARANITE': 'Laranite', 'QUANTAINIUM': 'Quantanium', 'QUARTZ': 'Quartz',
            'RICCITE': 'Riccite', 'SILICON': 'Silicon', 'STILERON': 'Stileron',
            'TARANITE': 'Taranite', 'TITANIUM': 'Titanium', 'TUNGSTEN': 'Tungsten'
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
                # Store calculation results and move to payout management
                await session_manager.update_session(self.session_id, {
                    'calculation_data': result,
                    'current_step': PayrollStep.PAYOUT_MANAGEMENT
                })
                
                # Show payout management view
                view = PayoutManagementView(self.session_id)
                embed = await view.create_embed()
                
                await interaction.edit_original_response(embed=embed, view=view)
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


class PayoutManagementView(ui.View):
    """Step 4: Payout Management - Individual participant payouts with donation controls."""
    
    def __init__(self, session_id: str):
        super().__init__(timeout=1800)  # 30 minutes
        self.session_id = session_id
        self.donation_states = {}  # Track donation states for participants
        
        # Add participant buttons dynamically in create_embed
        
    async def create_embed(self):
        """Create the payout management embed with participant list."""
        try:
            session = await session_manager.get_session(self.session_id)
            if not session:
                return self.create_error_embed("Session not found")
            
            calculation_data = session.get('calculation_data', {})
            if not calculation_data:
                return self.create_error_embed("No calculation data found")
            
            # Initialize donation states - prioritize session data over calculation data
            session_donation_states = session.get('donation_states', {})
            logger.info(f"Loading donation states - session has: {session_donation_states}")
            if session_donation_states:
                self.donation_states = session_donation_states
                logger.info(f"Loaded donation states from session: {self.donation_states}")
            else:
                # Fall back to calculation data for initial state
                for payout in calculation_data.get('payouts', []):
                    user_id = str(payout['user_id'])
                    self.donation_states[user_id] = payout.get('is_donor', False)
                logger.info(f"Initialized donation states from calculation data: {self.donation_states}")
            
            # Create embed with enhanced formatting and wider layout
            embed = discord.Embed(
                title="# 💰 Step 4: Payout Management",
                description=f"## **Event Management Dashboard**\n\n"
                          f"```yaml\n"
                          f"Event ID:      {calculation_data['event_data']['event_id']}\n"
                          f"Total Value:   {calculation_data['total_value_auec']:>15,.0f} aUEC\n"
                          f"Participants:  {calculation_data['total_participants']:>15}\n"
                          f"```\n"
                          f"**Click participant buttons to toggle donation status. Green = Donating, Gray = Receiving**\n"
                          f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                color=discord.Color.gold()
            )
            
            # Add participant payout details with live calculations
            payout_text = ""
            
            # First, recalculate all payouts with current donation states
            updated_payouts = self.recalculate_with_donations(calculation_data['payouts'], self.donation_states)
            
            total_donated = 0
            total_recipients = 0
            
            for payout in updated_payouts:
                username = payout['username']
                minutes = payout['participation_minutes']
                percentage = payout['participation_percentage']
                final_amount = float(payout['final_payout_auec'])
                is_donating = payout['is_donor']
                
                if is_donating:
                    payout_text += f"💝 **{username[:18]}** - {minutes:.0f}min ({percentage:.1f}%) → **DONATED**\n"
                    total_donated += float(payout['base_payout_auec'])
                else:
                    payout_text += f"💰 **{username[:18]}** - {minutes:.0f}min ({percentage:.1f}%) → **{final_amount:,.0f} aUEC**\n"
                    total_recipients += 1
            
            # Calculate bonus distribution with enhanced formatting
            if total_donated > 0 and total_recipients > 0:
                bonus_per_person = total_donated / total_recipients
                payout_text += f"\n```yaml\n"
                payout_text += f"Distribution Summary:\n"
                payout_text += f"  Donated Re-distribution: {total_donated:>12,.0f} aUEC\n"
                payout_text += f"  Bonus per Recipient:     {bonus_per_person:>12,.0f} aUEC\n"
                payout_text += f"```"
            
            embed.add_field(
                name="# 👥 **PARTICIPANT PAYOUTS**",
                value=payout_text[:1024] if payout_text else "No participants found",
                inline=False
            )
            
            # Add control buttons
            self.clear_items()
            self.add_participant_buttons(calculation_data['payouts'])
            self.add_control_buttons()
            
            return embed
            
        except Exception as e:
            logger.error(f"Error creating payout management embed: {e}")
            return self.create_error_embed(f"Error: {str(e)}")
    
    def recalculate_with_donations(self, original_payouts, donation_states):
        """Recalculate payouts based on current donation states."""
        updated_payouts = []
        total_donated = Decimal('0')
        recipients = []
        
        # First pass: identify donors and recipients
        for payout in original_payouts:
            user_id = str(payout['user_id'])
            is_donating = donation_states.get(user_id, False)
            base_payout = Decimal(str(payout['base_payout_auec']))
            
            updated_payout = {
                'user_id': payout['user_id'],
                'username': payout['username'],
                'participation_minutes': payout['participation_minutes'],
                'participation_percentage': payout['participation_percentage'],
                'base_payout_auec': base_payout,
                'is_donor': is_donating
            }
            
            if is_donating:
                total_donated += base_payout
                updated_payout['final_payout_auec'] = Decimal('0')
            else:
                recipients.append(updated_payout)
                updated_payout['final_payout_auec'] = base_payout  # Will be updated with bonus
            
            updated_payouts.append(updated_payout)
        
        # Second pass: distribute donated amounts to recipients
        if total_donated > 0 and recipients:
            bonus_per_recipient = total_donated / len(recipients)
            for payout in updated_payouts:
                if not payout['is_donor']:
                    payout['final_payout_auec'] += bonus_per_recipient
                    payout['final_payout_auec'] = payout['final_payout_auec'].quantize(Decimal('0.01'))
        
        return updated_payouts
    
    def add_participant_buttons(self, payouts):
        """Add toggle buttons for each participant."""
        for i, payout in enumerate(payouts):
            if i >= 20:  # Discord limit on buttons
                break
                
            user_id = str(payout['user_id'])
            username = payout['username']
            is_donating = self.donation_states.get(user_id, False)
            
            button = ParticipantDonationButton(
                user_id=user_id,
                username=username,
                is_donating=is_donating,
                session_id=self.session_id
            )
            self.add_item(button)
    
    def add_control_buttons(self):
        """Add main control buttons."""
        self.add_item(RecalculatePayoutsButton(self.session_id))
        self.add_item(FinalizePayrollButton(self.session_id))
        self.add_item(BackToCalculationButton(self.session_id))
        self.add_item(CancelSessionButton(self.session_id))
    
    def create_error_embed(self, message: str):
        """Create an error embed."""
        return discord.Embed(
            title="❌ Payout Management Error",
            description=message,
            color=discord.Color.red()
        )


class ParticipantDonationButton(ui.Button):
    """Button to toggle donation status for a participant."""
    
    def __init__(self, user_id: str, username: str, is_donating: bool, session_id: str):
        self.user_id = user_id
        self.username = username
        self.session_id = session_id
        
        # Set button appearance with clear visual feedback like custom pricing buttons
        if is_donating:
            super().__init__(
                label=f"{username[:15]} (Donating)",
                style=discord.ButtonStyle.success,  # Green for donating
                custom_id=f"donate_{user_id}",
                emoji="💝"
            )
        else:
            super().__init__(
                label=f"{username[:15]} (Receiving)",
                style=discord.ButtonStyle.secondary,   # Gray for receiving
                custom_id=f"receive_{user_id}",
                emoji="💰"
            )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            # Get parent view and toggle donation state
            old_view = self.view
            current_state = old_view.donation_states.get(self.user_id, False)
            new_state = not current_state
            old_view.donation_states[self.user_id] = new_state
            
            # Debug logging
            logger.info(f"Donation button clicked for {self.user_id} ({self.username}): {current_state} -> {new_state}")
            
            # Update session with new donation state
            await session_manager.update_session(old_view.session_id, {
                'donation_states': old_view.donation_states
            })
            logger.info(f"Updated session donation states: {old_view.donation_states}")
            
            # Create a completely new view - it will load the updated donation states from the session
            new_view = PayoutManagementView(old_view.session_id)
            embed = await new_view.create_embed()
            
            # Debug: verify new view loaded correct states
            logger.info(f"New view donation states: {new_view.donation_states}")
            
            await interaction.edit_original_response(embed=embed, view=new_view)
            logger.info(f"Successfully updated view for donation toggle")
            
        except Exception as e:
            logger.error(f"Error toggling donation for {self.user_id}: {e}")
            await interaction.followup.send(f"❌ Error updating donation status", ephemeral=True)


class RecalculatePayoutsButton(ui.Button):
    """Button to recalculate payouts with current donation settings."""
    
    def __init__(self, session_id: str):
        super().__init__(
            label="🔄 Update Distribution",
            style=discord.ButtonStyle.secondary,
            emoji="🔄"
        )
        self.session_id = session_id
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            view = self.view
            embed = await view.create_embed()
            await interaction.edit_original_response(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error recalculating payouts: {e}")
            await interaction.followup.send("❌ Error updating distribution", ephemeral=True)


class FinalizePayrollButton(ui.Button):
    """Button to finalize the payroll with current settings."""
    
    def __init__(self, session_id: str):
        super().__init__(
            label="✅ Finalize Payroll",
            style=discord.ButtonStyle.success,
            emoji="✅"
        )
        self.session_id = session_id
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            session = await session_manager.get_session(self.session_id)
            if not session:
                await interaction.followup.send("❌ Session not found", ephemeral=True)
                return
            
            calculation_data = session.get('calculation_data', {})
            view = self.view
            
            # Update payouts with current donation states and recalculate
            updated_payouts = view.recalculate_with_donations(calculation_data['payouts'], view.donation_states)
            
            # Complete session
            await session_manager.complete_calculation(self.session_id, {
                **calculation_data,
                'payouts': updated_payouts,
                'final_donation_states': view.donation_states
            })
            
            # Show final summary
            embed = discord.Embed(
                title="# ✅ Payroll Finalized!",
                description=f"## **Mining Session Complete**\n\n"
                          f"```yaml\n"
                          f"Event ID:      {calculation_data['event_data']['event_id']}\n"
                          f"Total Value:   {calculation_data['total_value_auec']:>15,.0f} aUEC\n"
                          f"Participants:  {calculation_data['total_participants']:>15}\n"
                          f"```\n"
                          f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            # Add final payout summary with enhanced formatting for multiple rows
            payout_lines = []
            total_donated_final = Decimal('0')
            
            # Create formatted table of payouts with better spacing and columns
            payout_lines.append("PARTICIPANT       STATUS            AMOUNT         TIME")
            payout_lines.append("─" * 58)
            
            for payout in updated_payouts:
                final_amount = payout['final_payout_auec']
                participation_minutes = payout['participation_minutes']
                username = payout['username'][:15]  # Limit username length for table alignment
                
                # Calculate total donated from updated payouts
                if payout.get('is_donor', False):
                    total_donated_final += payout['base_payout_auec']
                    payout_lines.append(f"{username:<16}  💝 DONATED       {'─':<13}  {participation_minutes:>3.0f} min")
                else:
                    payout_lines.append(f"{username:<16}  💰 RECEIVED      {final_amount:>10,.0f} aUEC  {participation_minutes:>3.0f} min")
            
            # Format payouts in code block for better alignment
            payout_summary = "```\n" + "\n".join(payout_lines) + "\n```"
            
            embed.add_field(
                name="💰 Final Payouts",
                value=payout_summary[:1024] if payout_summary else "No payouts",
                inline=False
            )
            
            embed.add_field(
                name="📊 Summary",
                value=f"**Payroll ID:** `{calculation_data['payroll_id']}`\n"
                      f"**Session Duration:** {calculation_data['total_minutes']} minutes\n"
                      f"**Donated Re-distribution Amount:** {total_donated_final:,.0f} aUEC",
                inline=False
            )
            
            await interaction.edit_original_response(embed=embed, view=None)
            
        except Exception as e:
            logger.error(f"Error finalizing payroll: {e}")
            await interaction.followup.send(f"❌ Error finalizing payroll: {str(e)}", ephemeral=True)


class BackToCalculationButton(ui.Button):
    """Button to go back to calculation review."""
    
    def __init__(self, session_id: str):
        super().__init__(
            label="⬅️ Back to Calculation",
            style=discord.ButtonStyle.secondary,
            emoji="⬅️"
        )
        self.session_id = session_id
    
    async def callback(self, interaction: discord.Interaction):
        # Update session step back to calculation review
        await session_manager.update_session(self.session_id, {
            'current_step': PayrollStep.CALCULATION_REVIEW
        })
        
        # Show calculation review view
        view = PricingReviewView(self.session_id)
        embed = await view.create_embed()
        
        await interaction.response.edit_message(embed=embed, view=view)


class CustomPricingView(ui.View):
    """Step 2.5: Custom Pricing - Allow modification of imported per-SCU prices."""
    
    def __init__(self, session_id: str):
        super().__init__(timeout=1800)  # 30 minutes
        self.session_id = session_id
        
    async def create_embed(self):
        """Create the custom pricing embed with ore price options."""
        try:
            session = await session_manager.get_session(self.session_id)
            if not session:
                return self.create_error_embed("Session not found")
            
            ore_quantities = session.get('ore_quantities', {})
            custom_prices = session.get('custom_prices', {})
            
            # Get current UEX prices for comparison
            processor = MiningProcessor()
            try:
                uex_prices = await processor.get_current_prices(refresh=True, allow_api_calls=True)
            except:
                uex_prices = {}
            
            # Create embed
            embed = discord.Embed(
                title="💎 Step 2.5: Custom Pricing (Optional)",
                description=f"**Event:** {session['event_id']}\n\n"
                          "Review and optionally override ore prices. "
                          "Default prices are from UEX Corp API.",
                color=discord.Color.purple()
            )
            
            # Show price options for ores with quantities > 0
            pricing_text = ""
            for ore_name, quantity in ore_quantities.items():
                if quantity > 0:
                    uex_price = uex_prices.get(ore_name.upper(), {}).get('price', 0)
                    custom_price = custom_prices.get(ore_name, uex_price)
                    
                    if custom_price != uex_price:
                        pricing_text += f"🔧 **{ore_name}:** {custom_price:,.1f} aUEC/SCU (Custom)\n"
                    else:
                        pricing_text += f"📊 **{ore_name}:** {uex_price:,.1f} aUEC/SCU (UEX API)\n"
            
            embed.add_field(
                name="💰 Current Pricing",
                value=pricing_text if pricing_text else "No ores selected",
                inline=False
            )
            
            # Add control buttons
            self.clear_items()
            self.add_ore_pricing_buttons(ore_quantities, custom_prices, uex_prices)
            self.add_navigation_buttons()
            
            return embed
            
        except Exception as e:
            logger.error(f"Error creating custom pricing embed: {e}")
            return self.create_error_embed(f"Error: {str(e)}")
    
    def add_ore_pricing_buttons(self, ore_quantities: Dict, custom_prices: Dict, uex_prices: Dict):
        """Add buttons for each ore with quantity > 0."""
        ore_count = 0
        for ore_name, quantity in ore_quantities.items():
            if quantity > 0 and ore_count < 20:  # Discord button limit
                uex_price = uex_prices.get(ore_name.upper(), {}).get('price', 0)
                current_price = custom_prices.get(ore_name, uex_price)
                is_custom = ore_name in custom_prices
                
                button = OrePriceButton(
                    ore_name=ore_name,
                    current_price=current_price,
                    session_id=self.session_id,
                    is_custom=is_custom
                )
                self.add_item(button)
                ore_count += 1
    
    def add_navigation_buttons(self):
        """Add main navigation buttons."""
        self.add_item(ContinueToPricingReviewButton(self.session_id))
        self.add_item(BackToQuantitiesFromPricingButton(self.session_id))
        self.add_item(CancelSessionButton(self.session_id))
    
    def create_error_embed(self, message: str):
        """Create an error embed."""
        return discord.Embed(
            title="❌ Custom Pricing Error",
            description=message,
            color=discord.Color.red()
        )


class OrePriceButton(ui.Button):
    """Button to set custom price for a specific ore."""
    
    def __init__(self, ore_name: str, current_price: float, session_id: str, is_custom: bool = False):
        self.ore_name = ore_name
        self.current_price = current_price
        self.session_id = session_id
        self.is_custom = is_custom
        
        # Show different style and emoji for custom vs UEX prices
        if is_custom:
            emoji = "🔧"
            style = discord.ButtonStyle.success
            label = f"{ore_name}: {current_price:,.0f} (Custom)"
        else:
            emoji = "💎"
            style = discord.ButtonStyle.secondary
            label = f"{ore_name}: {current_price:,.0f} (UEX)"
        
        super().__init__(
            label=label,
            style=style,
            emoji=emoji,
            custom_id=f"price_{ore_name}"
        )
    
    async def callback(self, interaction: discord.Interaction):
        # Show modal for custom price input
        modal = OrePriceModal(
            ore_name=self.ore_name,
            current_price=self.current_price,
            session_id=self.session_id
        )
        await interaction.response.send_modal(modal)


class OrePriceModal(ui.Modal):
    """Modal for entering custom ore price."""
    
    def __init__(self, ore_name: str, current_price: float, session_id: str):
        self.ore_name = ore_name
        self.session_id = session_id
        
        super().__init__(title=f"Set Price for {ore_name}")
        
        self.price_input = ui.TextInput(
            label="Price per SCU (aUEC)",
            placeholder=f"Current: {current_price:,.1f}",
            default=str(current_price),
            max_length=10,
            required=True
        )
        self.add_item(self.price_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            # Parse price with better validation
            price_str = self.price_input.value.replace(',', '').replace(' ', '').strip()
            if not price_str:
                await interaction.followup.send("❌ Price cannot be empty", ephemeral=True)
                return
                
            new_price = float(price_str)
            if new_price < 0:
                await interaction.followup.send("❌ Price cannot be negative", ephemeral=True)
                return
            
            # Update session with custom price using the standard update method
            session = await session_manager.get_session(self.session_id)
            if not session:
                await interaction.followup.send("❌ Session not found", ephemeral=True)
                return
                
            custom_prices = session.get('custom_prices', {})
            custom_prices[self.ore_name] = new_price
            
            # Use the standard update_session method instead of set_custom_pricing_data
            await session_manager.update_session(self.session_id, {'custom_prices': custom_prices})
            
            # Refresh the view
            view = CustomPricingView(self.session_id)
            embed = await view.create_embed()
            
            await interaction.edit_original_response(embed=embed, view=view)
            
        except ValueError as e:
            logger.error(f"ValueError setting custom price for {self.ore_name}: {e}")
            await interaction.followup.send("❌ Invalid price format. Please enter a valid number.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error setting custom price for {self.ore_name}: {e}")
            await interaction.followup.send(f"❌ Error setting custom price: {str(e)}", ephemeral=True)


class ContinueToPricingReviewButton(ui.Button):
    """Button to continue to final pricing review."""
    
    def __init__(self, session_id: str):
        super().__init__(
            label="Continue to Pricing Review",
            style=discord.ButtonStyle.success,
            emoji="📊"
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


class BackToQuantitiesFromPricingButton(ui.Button):
    """Button to go back to quantity entry from custom pricing."""
    
    def __init__(self, session_id: str):
        super().__init__(
            label="⬅️ Back to Quantities",
            style=discord.ButtonStyle.secondary,
            emoji="⬅️"
        )
        self.session_id = session_id
    
    async def callback(self, interaction: discord.Interaction):
        # Update session step back to quantity entry
        await session_manager.update_session(self.session_id, {
            'current_step': PayrollStep.QUANTITY_ENTRY
        })
        
        # Show quantity entry view
        session = await session_manager.get_session(self.session_id)
        event_type = session['event_type']
        
        # Import the appropriate processor
        processor = MiningProcessor()
        view = OreQuantityEntryView(self.session_id, processor)
        embed, quantity_view = await view.build_current_view()
        
        await interaction.response.edit_message(embed=embed, view=quantity_view)