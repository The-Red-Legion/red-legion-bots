"""
Payroll Collection Input Modals

Discord modals for collecting ore amounts, salvage data, and other materials.
"""

import discord
from discord import ui
from typing import Dict, Optional
from decimal import Decimal
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config.settings import ORE_TYPES

# Create organized ore lists
HIGH_VALUE_ORES = {
    'QUANTAINIUM': 'Quantainium',
    'BEXALITE': 'Bexalite', 
    'LARANITE': 'Laranite',
    'GOLD': 'Gold',
    'TARANITE': 'Taranite',
    'STILERON': 'Stileron',
    'RICCITE': 'Riccite'
}

MID_VALUE_ORES = {
    'AGRICIUM': 'Agricium',
    'BERYL': 'Beryl',
    'HEPHAESTANITE': 'Hephaestanite',
    'BORASE': 'Borase',
    'DIAMOND': 'Diamond'
}

COMMON_ORES = {
    'TUNGSTEN': 'Tungsten',
    'TITANIUM': 'Titanium',
    'IRON': 'Iron',
    'COPPER': 'Copper',
    'ALUMINUM': 'Aluminum',
    'SILICON': 'Silicon',
    'CORUNDUM': 'Corundum',
    'QUARTZ': 'Quartz',
    'TIN': 'Tin'
}

class MiningCollectionModal(ui.Modal):
    """Modal for inputting mining ore collections."""
    
    def __init__(self, event_data: Dict, processor, calculator):
        super().__init__(title=f'Mining Payroll - {event_data["event_id"]}')
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        
        # Create input fields for high-value ores
        self.quantainium = ui.TextInput(
            label='Quantainium (SCU)',
            placeholder='0.0',
            default='0',
            required=False,
            max_length=10
        )
        
        self.bexalite = ui.TextInput(
            label='Bexalite (SCU)', 
            placeholder='0.0',
            default='0',
            required=False,
            max_length=10
        )
        
        self.high_value_ores = ui.TextInput(
            label='High Value Ores (Laranite:5.2, Gold:3.1, Taranite:1.5)',
            placeholder='Laranite:0, Gold:0, Taranite:0, Stileron:0',
            required=False,
            max_length=200
        )
        
        self.mid_value_ores = ui.TextInput(
            label='Mid Value Ores (Agricium:10, Beryl:5, Hephaestanite:8)',
            placeholder='Agricium:0, Beryl:0, Hephaestanite:0, Borase:0',
            required=False,
            max_length=200
        )
        
        self.common_ores = ui.TextInput(
            label='Common Ores (Tungsten:20, Titanium:15, Iron:25, Copper:10)',
            placeholder='Tungsten:0, Titanium:0, Iron:0, Copper:0, Aluminum:0, Silicon:0',
            required=False,
            style=discord.TextStyle.paragraph,
            max_length=400
        )
        
        # Add all inputs to the modal
        self.add_item(self.quantainium)
        self.add_item(self.bexalite)
        self.add_item(self.high_value_ores)
        self.add_item(self.mid_value_ores)
        self.add_item(self.common_ores)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            # Parse ore collections
            ore_collections = {}
            
            # Parse main ore inputs
            main_ores = {
                'QUANTAINIUM': self.quantainium.value,
                'BEXALITE': self.bexalite.value
            }
            
            for ore_name, value in main_ores.items():
                if value and value.strip():
                    try:
                        amount = float(value.strip())
                        if amount > 0:
                            ore_collections[ore_name] = amount
                    except ValueError:
                        await interaction.followup.send(
                            f"❌ Invalid amount for {ore_name}: '{value}'",
                            ephemeral=True
                        )
                        return
            
            # Parse all ore category fields
            ore_fields = [
                self.high_value_ores.value,
                self.mid_value_ores.value,
                self.common_ores.value
            ]
            
            for field_value in ore_fields:
                if field_value and field_value.strip():
                    try:
                        # Handle both comma and space separated formats
                        pairs = field_value.replace(',', ' ').split()
                        for pair in pairs:
                            if ':' in pair:
                                ore_name, amount_str = pair.split(':', 1)
                                ore_name = ore_name.strip().upper()
                                amount = float(amount_str.strip())
                                if amount > 0:
                                    ore_collections[ore_name] = amount
                    except ValueError as e:
                        await interaction.followup.send(
                            f"❌ Error parsing ore field: {str(e)}\nFormat: 'OreName:Amount, OreName:Amount'",
                            ephemeral=True
                        )
                        return
            
            # Check if any ore was collected
            if not ore_collections:
                await interaction.followup.send(
                    "❌ No ore collections entered. Please enter at least one ore amount.",
                    ephemeral=True
                )
                return
            
            # Get current ore prices
            await interaction.followup.send(
                embed=discord.Embed(
                    title="⏳ Calculating Payroll...",
                    description="Fetching current ore prices and calculating distribution...",
                    color=discord.Color.blue()
                )
            )
            
            prices = await self.processor.get_current_prices()
            if not prices:
                await interaction.edit_original_response(
                    embed=discord.Embed(
                        title="❌ Price Data Unavailable",
                        description="Could not fetch ore prices from UEX Corp API or cache. Please try again later.",
                        color=discord.Color.red()
                    )
                )
                return
            
            # Calculate total value
            total_value, breakdown = await self.processor.calculate_total_value(ore_collections, prices)
            
            if total_value <= 0:
                await interaction.edit_original_response(
                    embed=discord.Embed(
                        title="❌ No Valid Ore Values",
                        description="Could not calculate value for any of the entered ores. Check ore names and try again.",
                        color=discord.Color.red()
                    )
                )
                return
            
            # Show calculation results and get donation preference
            await self._show_payroll_summary(
                interaction, 
                ore_collections, 
                prices, 
                total_value, 
                breakdown
            )
            
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error Processing Collection Data",
                    description=f"An error occurred: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
    
    async def _show_payroll_summary(
        self, 
        interaction: discord.Interaction,
        ore_collections: Dict[str, float],
        prices: Dict[str, Dict],
        total_value: Decimal,
        breakdown: Dict
    ):
        """Show payroll calculation summary and get confirmation."""
        from .views import PayrollConfirmationView
        
        # Get participants count
        participants = await self.calculator.get_event_participants(self.event_data['event_id'])
        
        embed = discord.Embed(
            title=f"💰 Payroll Calculation - {self.event_data['event_id']}",
            description=f"**Total Value:** {total_value:,.2f} aUEC",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="📋 Event Details",
            value=f"**Event:** {self.event_data['event_name']}\n"
                  f"**Organizer:** {self.event_data['organizer_name']}\n"
                  f"**Participants:** {len(participants)}",
            inline=True
        )
        
        # Show ore breakdown
        if len(breakdown) <= 6:  # Show all if few ores
            ore_text = []
            for ore_name, data in breakdown.items():
                ore_text.append(f"**{ore_name}:** {data['scu_amount']} SCU @ {data['price_per_scu']:,.0f} = {data['total_value']:,.0f} aUEC")
            
            embed.add_field(
                name="⛏️ Ore Collections",
                value="\n".join(ore_text),
                inline=False
            )
        else:  # Summarize if many ores
            total_scu = sum(data['scu_amount'] for data in breakdown.values())
            embed.add_field(
                name="⛏️ Ore Collections",
                value=f"**Total:** {total_scu:.1f} SCU across {len(breakdown)} ore types\n"
                      f"Use `/payroll status` to see detailed breakdown",
                inline=False
            )
        
        embed.add_field(
            name="🔄 Next Step",
            value="Choose donation percentage and confirm calculation",
            inline=False
        )
        
        # Create confirmation view with donation options
        view = PayrollConfirmationView(
            event_data=self.event_data,
            ore_collections=ore_collections,
            prices=prices,
            total_value=total_value,
            breakdown=breakdown,
            processor=self.processor,
            calculator=self.calculator
        )
        
        await interaction.edit_original_response(embed=embed, view=view)


# =====================================================
# SOLUTION 3: TWO-STAGE ORE SELECTION SYSTEM
# Stage 1: Checkbox selection of ore types
# Stage 2: Amount input modal for selected ores only
# =====================================================

class TwoStageOreSelectionView(ui.View):
    """Stage 1: Checkbox selection of which ore types were collected."""
    
    def __init__(self, event_data: Dict, processor, calculator):
        super().__init__(timeout=600)
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.selected_ores = set()  # Track which ores are selected
        
        # Add ore selection dropdowns (using multiple dropdowns due to 25 option limit)
        self.add_item(HighValueOreSelector(self.selected_ores))
        self.add_item(MidValueOreSelector(self.selected_ores))
        self.add_item(CommonOreSelector(self.selected_ores))
        
        # Add proceed button (initially disabled)
        proceed_button = ProceedToAmountsButton(event_data, processor, calculator, self.selected_ores)
        proceed_button.disabled = True
        self.add_item(proceed_button)
        
        # Add cancel button
        self.add_item(CancelOreSelectionButton())
    
    def update_proceed_button(self):
        """Enable/disable proceed button based on selections."""
        for item in self.children:
            if isinstance(item, ProceedToAmountsButton):
                item.disabled = len(self.selected_ores) == 0


class HighValueOreSelector(ui.Select):
    """Dropdown for selecting high-value ores."""
    
    def __init__(self, selected_ores: set):
        self.selected_ores = selected_ores
        
        options = []
        for ore_code, ore_name in HIGH_VALUE_ORES.items():
            options.append(discord.SelectOption(
                label=ore_name,
                description=f"High value ore • Select if collected",
                value=ore_code,
                emoji="⭐"
            ))
        
        super().__init__(
            placeholder="Select high value ores collected...",
            options=options,
            min_values=0,
            max_values=len(options)  # Allow multiple selections
        )
    
    async def callback(self, interaction: discord.Interaction):
        # Update selected ores
        for ore_code in list(self.selected_ores):
            if ore_code in HIGH_VALUE_ORES and ore_code not in self.values:
                self.selected_ores.remove(ore_code)
        
        for ore_code in self.values:
            self.selected_ores.add(ore_code)
        
        # Update proceed button and refresh the view
        self.view.update_proceed_button()
        
        # Show selection feedback and update the view
        if self.values:
            selected_names = [HIGH_VALUE_ORES[code] for code in self.values]
            await interaction.response.send_message(
                f"✅ Selected high-value ores: **{', '.join(selected_names)}**\n"
                f"Total selected: **{len(self.selected_ores)} ore types**\n"
                f"💡 Click **Enter Amounts** when ready to proceed!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "⭕ Cleared high-value ore selections.",
                ephemeral=True
            )
        
        # Force update the view to refresh button states
        try:
            await interaction.edit_original_response(view=self.view)
        except:
            pass  # Might fail if this is a followup, that's OK


class MidValueOreSelector(ui.Select):
    """Dropdown for selecting mid-value ores."""
    
    def __init__(self, selected_ores: set):
        self.selected_ores = selected_ores
        
        options = []
        for ore_code, ore_name in MID_VALUE_ORES.items():
            options.append(discord.SelectOption(
                label=ore_name,
                description=f"Mid value ore • Select if collected",
                value=ore_code,
                emoji="🟡"
            ))
        
        super().__init__(
            placeholder="Select mid value ores collected...",
            options=options,
            min_values=0,
            max_values=len(options)
        )
    
    async def callback(self, interaction: discord.Interaction):
        # Update selected ores
        for ore_code in list(self.selected_ores):
            if ore_code in MID_VALUE_ORES and ore_code not in self.values:
                self.selected_ores.remove(ore_code)
        
        for ore_code in self.values:
            self.selected_ores.add(ore_code)
        
        # Update proceed button and refresh the view
        self.view.update_proceed_button()
        
        # Show selection feedback and update the view
        if self.values:
            selected_names = [MID_VALUE_ORES[code] for code in self.values]
            await interaction.response.send_message(
                f"✅ Selected mid-value ores: **{', '.join(selected_names)}**\n"
                f"Total selected: **{len(self.selected_ores)} ore types**\n"
                f"💡 Click **Enter Amounts** when ready to proceed!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "⭕ Cleared mid-value ore selections.",
                ephemeral=True
            )
        
        # Force update the view to refresh button states
        try:
            await interaction.edit_original_response(view=self.view)
        except:
            pass  # Might fail if this is a followup, that's OK


class CommonOreSelector(ui.Select):
    """Dropdown for selecting common ores."""
    
    def __init__(self, selected_ores: set):
        self.selected_ores = selected_ores
        
        options = []
        # Limit to first 12 common ores to fit Discord's limits
        for ore_code, ore_name in list(COMMON_ORES.items())[:12]:
            options.append(discord.SelectOption(
                label=ore_name,
                description=f"Common ore • Select if collected",
                value=ore_code,
                emoji="🟢"
            ))
        
        super().__init__(
            placeholder="Select common ores collected...",
            options=options,
            min_values=0,
            max_values=len(options)
        )
    
    async def callback(self, interaction: discord.Interaction):
        # Update selected ores
        for ore_code in list(self.selected_ores):
            if ore_code in COMMON_ORES and ore_code not in self.values:
                self.selected_ores.remove(ore_code)
        
        for ore_code in self.values:
            self.selected_ores.add(ore_code)
        
        # Update proceed button and refresh the view
        self.view.update_proceed_button()
        
        # Show selection feedback and update the view
        if self.values:
            selected_names = [COMMON_ORES[code] for code in self.values if code in COMMON_ORES]
            await interaction.response.send_message(
                f"✅ Selected common ores: **{', '.join(selected_names)}**\n"
                f"Total selected: **{len(self.selected_ores)} ore types**\n"
                f"💡 Click **Enter Amounts** when ready to proceed!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "⭕ Cleared common ore selections.",
                ephemeral=True
            )
        
        # Force update the view to refresh button states
        try:
            await interaction.edit_original_response(view=self.view)
        except:
            pass  # Might fail if this is a followup, that's OK


class ProceedToAmountsButton(ui.Button):
    """Button to proceed to Stage 2: Amount input modal."""
    
    def __init__(self, event_data: Dict, processor, calculator, selected_ores: set):
        super().__init__(
            label="Enter Amounts →",
            style=discord.ButtonStyle.primary,
            emoji="📝"
        )
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.selected_ores = selected_ores
    
    async def callback(self, interaction: discord.Interaction):
        if not self.selected_ores:
            await interaction.response.send_message(
                "❌ Please select at least one ore type before proceeding.",
                ephemeral=True
            )
            return
        
        # Create dynamic modal with fields for selected ores only
        amounts_modal = DynamicOreAmountsModal(
            self.event_data, 
            self.processor, 
            self.calculator, 
            list(self.selected_ores)
        )
        
        # Disable all buttons in current view
        for item in self.view.children:
            item.disabled = True
        
        await interaction.response.send_modal(amounts_modal)


class DynamicOreAmountsModal(ui.Modal):
    """Stage 2: Dynamic modal with amount fields for only the selected ores."""
    
    def __init__(self, event_data: Dict, processor, calculator, selected_ore_codes: list):
        # Create title showing how many ores
        ore_count = len(selected_ore_codes)
        super().__init__(title=f'Ore Amounts ({ore_count} types)')
        
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.selected_ore_codes = selected_ore_codes
        self.ore_inputs = {}
        
        # Create input fields for selected ores (max 5 per modal due to Discord limits)
        ore_fields_added = 0
        
        for ore_code in selected_ore_codes[:5]:  # Discord modal limit
            ore_name = (HIGH_VALUE_ORES.get(ore_code) or 
                       MID_VALUE_ORES.get(ore_code) or 
                       COMMON_ORES.get(ore_code) or ore_code)
            
            # Create input field
            ore_input = ui.TextInput(
                label=f'{ore_name} (SCU)',
                placeholder='Enter SCU amount (e.g., 5.2, 10, 15.7)',
                required=True,
                max_length=10
            )
            
            self.ore_inputs[ore_code] = ore_input
            self.add_item(ore_input)
            ore_fields_added += 1
        
        # If more than 5 ores selected, we'll need multi-modal approach
        self.remaining_ores = selected_ore_codes[5:] if len(selected_ore_codes) > 5 else []
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            # Parse amounts from current modal
            ore_collections = {}
            
            for ore_code, input_field in self.ore_inputs.items():
                try:
                    amount = float(input_field.value.strip())
                    if amount > 0:
                        ore_collections[ore_code] = amount
                except ValueError:
                    await interaction.followup.send(
                        f"❌ Invalid amount for {ore_code}: '{input_field.value}'",
                        ephemeral=True
                    )
                    return
            
            # If there are remaining ores, show another modal
            if self.remaining_ores:
                # Store current amounts and show modal for remaining ores
                remaining_modal = DynamicOreAmountsModalContinuation(
                    self.event_data, 
                    self.processor, 
                    self.calculator,
                    ore_collections,  # Pass current amounts
                    self.remaining_ores
                )
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="📝 More Ores to Enter",
                        description=f"Saved amounts for first batch.\nNow enter amounts for remaining {len(self.remaining_ores)} ore types.",
                        color=discord.Color.blue()
                    ),
                    ephemeral=True
                )
                # Note: Can't chain modals directly, user needs to trigger next modal
                # This is a Discord limitation - we'd need a button to continue
                return
            
            # No remaining ores, proceed with payroll calculation
            if not ore_collections:
                await interaction.followup.send(
                    "❌ No valid ore amounts entered.",
                    ephemeral=True
                )
                return
            
            await self._proceed_with_payroll_calculation(interaction, ore_collections)
            
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error Processing Ore Amounts",
                    description=f"An error occurred: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
    
    async def _proceed_with_payroll_calculation(self, interaction: discord.Interaction, ore_collections: Dict):
        """Proceed with payroll calculation using collected ore amounts."""
        try:
            # Get current ore prices
            await interaction.followup.send(
                embed=discord.Embed(
                    title="⏳ Calculating Payroll...",
                    description="Fetching current ore prices and calculating distribution...",
                    color=discord.Color.blue()
                )
            )
            
            prices = await self.processor.get_current_prices()
            if not prices:
                await interaction.edit_original_response(
                    embed=discord.Embed(
                        title="❌ Price Data Unavailable",
                        description="Could not fetch ore prices from UEX Corp API or cache. Please try again later.",
                        color=discord.Color.red()
                    )
                )
                return
            
            # Calculate total value
            total_value, breakdown = await self.processor.calculate_total_value(ore_collections, prices)
            
            if total_value <= 0:
                await interaction.edit_original_response(
                    embed=discord.Embed(
                        title="❌ No Valid Ore Values", 
                        description="Could not calculate value for any of the entered ores. Check ore names and try again.",
                        color=discord.Color.red()
                    )
                )
                return
            
            # Show payroll summary
            from .views import PayrollConfirmationView
            
            # Get participants count
            participants = await self.calculator.get_event_participants(self.event_data['event_id'])
            
            embed = discord.Embed(
                title=f"💰 Payroll Calculation - {self.event_data['event_id']}",
                description=f"**Total Value:** {total_value:,.2f} aUEC",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📋 Event Details",
                value=f"**Event:** {self.event_data['event_name']}\n"
                      f"**Organizer:** {self.event_data['organizer_name']}\n"
                      f"**Participants:** {len(participants)}",
                inline=True
            )
            
            # Show ore breakdown
            ore_text = []
            total_scu = 0
            for ore_code, amount in ore_collections.items():
                ore_name = (HIGH_VALUE_ORES.get(ore_code) or 
                           MID_VALUE_ORES.get(ore_code) or 
                           COMMON_ORES.get(ore_code) or ore_code)
                if ore_code.upper() in breakdown:
                    data = breakdown[ore_code.upper()]
                    ore_text.append(f"**{ore_name}:** {amount} SCU @ {data['price_per_scu']:,.0f} = {data['total_value']:,.0f} aUEC")
                    total_scu += amount
            
            embed.add_field(
                name="⛏️ Ore Collections",
                value="\n".join(ore_text[:8]) + (f"\n... and {len(ore_text) - 8} more" if len(ore_text) > 8 else ""),
                inline=False
            )
            
            embed.add_field(
                name="🔄 Next Step",
                value="Choose donation percentage and confirm calculation",
                inline=False
            )
            
            # Create confirmation view
            view = PayrollConfirmationView(
                event_data=self.event_data,
                ore_collections=ore_collections,
                prices=prices,
                total_value=total_value,
                breakdown=breakdown,
                processor=self.processor,
                calculator=self.calculator
            )
            
            await interaction.edit_original_response(embed=embed, view=view)
            
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error Calculating Payroll",
                    description=f"An error occurred: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )


class DynamicOreAmountsModalContinuation(ui.Modal):
    """Continuation modal for when more than 5 ores are selected."""
    
    def __init__(self, event_data: Dict, processor, calculator, existing_amounts: Dict, remaining_ore_codes: list):
        super().__init__(title=f'More Ore Amounts ({len(remaining_ore_codes)} left)')
        
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.existing_amounts = existing_amounts
        self.remaining_ore_codes = remaining_ore_codes
        self.ore_inputs = {}
        
        # Create fields for remaining ores (max 5)
        for ore_code in remaining_ore_codes[:5]:
            ore_name = (HIGH_VALUE_ORES.get(ore_code) or 
                       MID_VALUE_ORES.get(ore_code) or 
                       COMMON_ORES.get(ore_code) or ore_code)
            
            ore_input = ui.TextInput(
                label=f'{ore_name} (SCU)',
                placeholder='Enter SCU amount',
                required=True,
                max_length=10
            )
            
            self.ore_inputs[ore_code] = ore_input
            self.add_item(ore_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        # Combine existing amounts with new ones and proceed
        # Implementation similar to main modal
        pass


# =====================================================  
# OLD STEP-BY-STEP SYSTEM (keeping for reference)
# =====================================================

class OreSelectionView(ui.View):
    """View for step-by-step ore selection with dropdown + amount system."""
    
    def __init__(self, event_data: Dict, processor, calculator):
        super().__init__(timeout=600)
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.ore_collections = {}  # Stores selected ores and amounts
        
        # Add ore selection dropdown
        self.add_item(OreSelectionDropdown(self.ore_collections))
        
        # Add finish button (initially disabled)
        finish_button = FinishOreSelectionButton(event_data, processor, calculator, self.ore_collections)
        finish_button.disabled = True
        self.add_item(finish_button)
        
        # Add cancel button
        self.add_item(CancelOreSelectionButton())
    
    def update_view(self):
        """Update the view based on current ore selections."""
        # Enable/disable finish button based on whether ores are selected
        for item in self.children:
            if isinstance(item, FinishOreSelectionButton):
                item.disabled = len(self.ore_collections) == 0


class OreSelectionDropdown(ui.Select):
    """Dropdown for selecting ore types."""
    
    def __init__(self, ore_collections: Dict):
        self.ore_collections = ore_collections
        
        # Create organized options
        options = []
        
        # High value ores
        options.append(discord.SelectOption(
            label="── High Value Ores ──",
            description="Premium ores with highest aUEC value",
            value="separator_high",
            emoji="💎"
        ))
        
        for ore_code, ore_name in HIGH_VALUE_ORES.items():
            options.append(discord.SelectOption(
                label=ore_name,
                description=f"High value ore • {ore_code}",
                value=f"high_{ore_code}",
                emoji="⭐"
            ))
        
        # Mid value ores  
        options.append(discord.SelectOption(
            label="── Mid Value Ores ──",
            description="Moderate value ores",
            value="separator_mid", 
            emoji="🔸"
        ))
        
        for ore_code, ore_name in MID_VALUE_ORES.items():
            options.append(discord.SelectOption(
                label=ore_name,
                description=f"Mid value ore • {ore_code}",
                value=f"mid_{ore_code}",
                emoji="🟡"
            ))
        
        # Common ores (limit to fit Discord's 25 option limit)
        options.append(discord.SelectOption(
            label="── Common Ores ──",
            description="High volume, lower value ores",
            value="separator_common",
            emoji="🔹"
        ))
        
        for ore_code, ore_name in list(COMMON_ORES.items())[:8]:  # Limit to fit in 25 total
            options.append(discord.SelectOption(
                label=ore_name,
                description=f"Common ore • {ore_code}",
                value=f"common_{ore_code}",
                emoji="🟢"
            ))
        
        super().__init__(
            placeholder="Choose an ore type to add...",
            options=options,
            min_values=1,
            max_values=1
        )
    
    async def callback(self, interaction: discord.Interaction):
        selected_value = self.values[0]
        
        # Skip separators
        if selected_value.startswith("separator_"):
            await interaction.response.send_message(
                "❌ Please select an actual ore, not a category header.",
                ephemeral=True
            )
            return
        
        # Parse selection
        category, ore_code = selected_value.split('_', 1)
        ore_name = HIGH_VALUE_ORES.get(ore_code) or MID_VALUE_ORES.get(ore_code) or COMMON_ORES.get(ore_code)
        
        if not ore_name:
            await interaction.response.send_message(
                "❌ Invalid ore selection.",
                ephemeral=True
            )
            return
        
        # Show amount input modal
        amount_modal = OreAmountModal(ore_code, ore_name, self.ore_collections, self.view)
        await interaction.response.send_modal(amount_modal)


class OreAmountModal(ui.Modal):
    """Modal for inputting the amount of a specific ore."""
    
    def __init__(self, ore_code: str, ore_name: str, ore_collections: Dict, parent_view):
        super().__init__(title=f'Add {ore_name}')
        self.ore_code = ore_code
        self.ore_name = ore_name
        self.ore_collections = ore_collections
        self.parent_view = parent_view
        
        # Amount input
        self.amount_input = ui.TextInput(
            label=f'{ore_name} Amount (SCU)',
            placeholder='Enter SCU amount (e.g., 5.2, 10, 15.7)',
            required=True,
            max_length=10
        )
        
        self.add_item(self.amount_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = float(self.amount_input.value.strip())
            if amount <= 0:
                await interaction.response.send_message(
                    "❌ Amount must be greater than 0.",
                    ephemeral=True
                )
                return
            
            # Add to collections
            self.ore_collections[self.ore_code] = amount
            
            # Update the parent view
            self.parent_view.update_view()
            
            # Show updated summary
            await self._show_updated_summary(interaction)
            
        except ValueError:
            await interaction.response.send_message(
                f"❌ Invalid amount: '{self.amount_input.value}'\nPlease enter a valid number.",
                ephemeral=True
            )
    
    async def _show_updated_summary(self, interaction: discord.Interaction):
        """Show the updated ore collection summary."""
        embed = discord.Embed(
            title="✅ Ore Added Successfully",
            description=f"Added **{self.ore_collections[self.ore_code]:.2f} SCU** of **{self.ore_name}**",
            color=discord.Color.green()
        )
        
        if len(self.ore_collections) > 1:
            # Show current collections
            ore_list = []
            total_scu = 0
            
            for ore_code, amount in self.ore_collections.items():
                ore_name = (HIGH_VALUE_ORES.get(ore_code) or 
                           MID_VALUE_ORES.get(ore_code) or 
                           COMMON_ORES.get(ore_code) or ore_code)
                ore_list.append(f"• **{ore_name}:** {amount:.2f} SCU")
                total_scu += amount
            
            embed.add_field(
                name=f"📦 Current Collection ({len(self.ore_collections)} ores)",
                value="\n".join(ore_list[:10]) + (f"\n... and {len(self.ore_collections) - 10} more" if len(self.ore_collections) > 10 else ""),
                inline=False
            )
            
            embed.add_field(
                name="📊 Total SCU",
                value=f"{total_scu:.2f} SCU",
                inline=True
            )
        
        embed.add_field(
            name="🔄 Next Steps",
            value="• Select another ore to add more\n• Click **Finish Collection** when done",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


class FinishOreSelectionButton(ui.Button):
    """Button to finish ore selection and proceed to payroll calculation."""
    
    def __init__(self, event_data: Dict, processor, calculator, ore_collections: Dict):
        super().__init__(
            label="Finish Collection",
            style=discord.ButtonStyle.success,
            emoji="✅"
        )
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.ore_collections = ore_collections
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        if not self.ore_collections:
            await interaction.followup.send(
                "❌ No ores selected. Please select at least one ore before finishing.",
                ephemeral=True
            )
            return
        
        # Proceed with payroll calculation (same as old modal)
        try:
            # Get current ore prices
            await interaction.followup.send(
                embed=discord.Embed(
                    title="⏳ Calculating Payroll...",
                    description="Fetching current ore prices and calculating distribution...",
                    color=discord.Color.blue()
                )
            )
            
            prices = await self.processor.get_current_prices()
            if not prices:
                await interaction.edit_original_response(
                    embed=discord.Embed(
                        title="❌ Price Data Unavailable",
                        description="Could not fetch ore prices from UEX Corp API or cache. Please try again later.",
                        color=discord.Color.red()
                    )
                )
                return
            
            # Calculate total value
            total_value, breakdown = await self.processor.calculate_total_value(self.ore_collections, prices)
            
            if total_value <= 0:
                await interaction.edit_original_response(
                    embed=discord.Embed(
                        title="❌ No Valid Ore Values",
                        description="Could not calculate value for any of the entered ores. Check ore names and try again.",
                        color=discord.Color.red()
                    )
                )
                return
            
            # Show payroll summary
            from .views import PayrollConfirmationView
            
            # Get participants count
            participants = await self.calculator.get_event_participants(self.event_data['event_id'])
            
            embed = discord.Embed(
                title=f"💰 Payroll Calculation - {self.event_data['event_id']}",
                description=f"**Total Value:** {total_value:,.2f} aUEC",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📋 Event Details",
                value=f"**Event:** {self.event_data['event_name']}\n"
                      f"**Organizer:** {self.event_data['organizer_name']}\n"
                      f"**Participants:** {len(participants)}",
                inline=True
            )
            
            # Show ore breakdown
            ore_text = []
            total_scu = 0
            for ore_code, amount in self.ore_collections.items():
                ore_name = (HIGH_VALUE_ORES.get(ore_code) or 
                           MID_VALUE_ORES.get(ore_code) or 
                           COMMON_ORES.get(ore_code) or ore_code)
                if ore_code.upper() in breakdown:
                    data = breakdown[ore_code.upper()]
                    ore_text.append(f"**{ore_name}:** {amount} SCU @ {data['price_per_scu']:,.0f} = {data['total_value']:,.0f} aUEC")
                    total_scu += amount
            
            embed.add_field(
                name="⛏️ Ore Collections",
                value="\n".join(ore_text[:8]) + (f"\n... and {len(ore_text) - 8} more" if len(ore_text) > 8 else ""),
                inline=False
            )
            
            embed.add_field(
                name="🔄 Next Step",
                value="Choose donation percentage and confirm calculation",
                inline=False
            )
            
            # Create confirmation view
            view = PayrollConfirmationView(
                event_data=self.event_data,
                ore_collections=self.ore_collections,
                prices=prices,
                total_value=total_value,
                breakdown=breakdown,
                processor=self.processor,
                calculator=self.calculator
            )
            
            # Disable all buttons in current view
            for item in self.view.children:
                item.disabled = True
            
            await interaction.edit_original_response(embed=embed, view=view)
            
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error Processing Collection Data",
                    description=f"An error occurred: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )


class CancelOreSelectionButton(ui.Button):
    """Button to cancel ore selection."""
    
    def __init__(self):
        super().__init__(
            label="Cancel",
            style=discord.ButtonStyle.secondary,
            emoji="❌"
        )
    
    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="❌ Ore Selection Cancelled",
            description="Payroll calculation has been cancelled.",
            color=discord.Color.orange()
        )
        
        # Disable all buttons
        for item in self.view.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self.view)


class PriceEditModal(ui.Modal):
    """Modal for editing ore prices in payroll calculation."""
    
    def __init__(self, event_data, ore_collections, prices, breakdown, processor, calculator, parent_view):
        super().__init__(title=f'Edit Prices - {event_data["event_id"]}')
        self.event_data = event_data
        self.ore_collections = ore_collections
        self.prices = prices
        self.breakdown = breakdown
        self.processor = processor
        self.calculator = calculator
        self.parent_view = parent_view
        self.price_inputs = {}
        
        # Create price input fields for collected ores (max 5 due to Discord modal limit)
        ore_count = 0
        for ore_name, data in breakdown.items():
            if ore_count >= 5:
                break
                
            current_price = data['price_per_scu']
            price_input = ui.TextInput(
                label=f'{ore_name} Price per SCU',
                placeholder=f'Current: {current_price:,.0f} aUEC',
                default=str(int(current_price)),
                required=True,
                max_length=10
            )
            
            self.price_inputs[ore_name] = price_input
            self.add_item(price_input)
            ore_count += 1
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            # Parse new prices
            updated_prices = {}
            for ore_name, input_field in self.price_inputs.items():
                try:
                    new_price = float(input_field.value.strip())
                    if new_price <= 0:
                        await interaction.followup.send(
                            f"❌ Price for {ore_name} must be greater than 0.",
                            ephemeral=True
                        )
                        return
                    updated_prices[ore_name] = new_price
                except ValueError:
                    await interaction.followup.send(
                        f"❌ Invalid price for {ore_name}: '{input_field.value}'",
                        ephemeral=True
                    )
                    return
            
            # Update prices in breakdown
            new_breakdown = {}
            total_value = 0
            
            for ore_name, data in self.breakdown.items():
                if ore_name in updated_prices:
                    new_price = updated_prices[ore_name]
                    new_total = data['scu_amount'] * new_price
                    new_breakdown[ore_name] = {
                        'scu_amount': data['scu_amount'],
                        'price_per_scu': new_price,
                        'total_value': new_total
                    }
                    total_value += new_total
                else:
                    new_breakdown[ore_name] = data
                    total_value += data['total_value']
            
            # Update parent view with new values
            self.parent_view.breakdown = new_breakdown
            self.parent_view.total_value = total_value
            
            # Update confirm button with new values
            for item in self.parent_view.children:
                if hasattr(item, 'total_value'):
                    item.total_value = total_value
                    item.breakdown = new_breakdown
            
            # Create updated embed
            embed = discord.Embed(
                title=f"💰 Payroll Calculation - {self.event_data['event_id']} (Prices Updated)",
                description=f"**Total Value:** {total_value:,.2f} aUEC",
                color=discord.Color.green()
            )
            
            # Get participants count
            participants = await self.calculator.get_event_participants(self.event_data['event_id'])
            
            embed.add_field(
                name="📋 Event Details",
                value=f"**Event:** {self.event_data['event_name']}\n"
                      f"**Organizer:** {self.event_data['organizer_name']}\n"
                      f"**Participants:** {len(participants)}",
                inline=True
            )
            
            # Show updated ore breakdown
            ore_text = []
            for ore_name, data in new_breakdown.items():
                price_changed = ore_name in updated_prices
                price_indicator = " ✏️" if price_changed else ""
                ore_text.append(f"**{ore_name}:** {data['scu_amount']} SCU @ {data['price_per_scu']:,.0f}{price_indicator} = {data['total_value']:,.0f} aUEC")
            
            embed.add_field(
                name="⛏️ Ore Collections",
                value="\n".join(ore_text[:8]) + (f"\n... and {len(ore_text) - 8} more" if len(ore_text) > 8 else ""),
                inline=False
            )
            
            embed.add_field(
                name="🔄 Next Step",
                value="Choose donation percentage and confirm calculation\n✏️ = Price manually edited",
                inline=False
            )
            
            await interaction.edit_original_response(embed=embed, view=self.parent_view)
            
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error Updating Prices",
                    description=f"An error occurred: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )


class ImprovedOreSelectionView(ui.View):
    """Improved 5-step ore selection workflow for mining payroll."""
    
    def __init__(self, event_data: Dict, processor, calculator):
        super().__init__(timeout=600)
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.selected_ores = set()
        self.step = 2  # Step 2: Ore Selection
        
        # Add alphabetical ore selection dropdown
        self.add_item(AlphabeticalOreSelector(self.selected_ores, self))
        
        # Add next button (initially disabled)
        next_button = NextToQuantitiesButton(self.event_data, self.processor, self.calculator, self.selected_ores, self)
        next_button.disabled = True
        self.add_item(next_button)
        
        # Add cancel button
        self.add_item(CancelButton())
    
    def update_next_button(self):
        """Enable/disable next button based on selections."""
        for item in self.children:
            if isinstance(item, NextToQuantitiesButton):
                item.disabled = len(self.selected_ores) == 0


class AlphabeticalOreSelector(ui.Select):
    """Single dropdown with all ores in alphabetical order."""
    
    def __init__(self, selected_ores: set, parent_view):
        self.selected_ores = selected_ores
        self.parent_view = parent_view
        
        # All ores in alphabetical order (no groupings)
        all_ores = {
            'AGRI': 'Agricium',
            'ALUM': 'Aluminum', 
            'BERY': 'Beryl',
            'BEXA': 'Bexalite',
            'BORA': 'Borase',
            'COPP': 'Copper',
            'DIAM': 'Diamond',
            'GOLD': 'Gold',
            'HADA': 'Hadanite',
            'HEPH': 'Hephaestanite',
            'INRT': 'Inert Materials',
            'LARA': 'Laranite',
            'QUAN': 'Quantanium',
            'TARA': 'Taranite',
            'TITA': 'Titanium',
            'TUNG': 'Tungsten'
        }
        
        # Sort by full name alphabetically
        sorted_ores = sorted(all_ores.items(), key=lambda x: x[1])
        
        options = []
        for ore_code, ore_name in sorted_ores:
            options.append(discord.SelectOption(
                label=ore_name,
                description=f"Select if {ore_name} was collected",
                value=ore_code,
                emoji="⛏️"
            ))
        
        super().__init__(
            placeholder="Select ore types that were collected...",
            options=options,
            min_values=0,
            max_values=len(options)  # Allow selecting all ores
        )
    
    async def callback(self, interaction: discord.Interaction):
        # Update selected ores
        self.selected_ores.clear()
        self.selected_ores.update(self.values)
        
        # Update parent view button states
        self.parent_view.update_next_button()
        
        # Show selection feedback
        if self.values:
            ore_names = []
            all_ores = {
                'AGRI': 'Agricium', 'ALUM': 'Aluminum', 'BERY': 'Beryl', 'BEXA': 'Bexalite',
                'BORA': 'Borase', 'COPP': 'Copper', 'DIAM': 'Diamond', 'GOLD': 'Gold',
                'HADA': 'Hadanite', 'HEPH': 'Hephaestanite', 'INRT': 'Inert Materials',
                'LARA': 'Laranite', 'QUAN': 'Quantanium', 'TARA': 'Taranite', 
                'TITA': 'Titanium', 'TUNG': 'Tungsten'
            }
            
            for code in self.values:
                ore_names.append(all_ores.get(code, code))
            
            embed = discord.Embed(
                title=f"⛏️ Mining Payroll - {self.parent_view.event_data['event_id']}",
                description=f"**Step 1 of 5: Event Selected** ✅\n"
                           f"**Step 2 of 5: Select Ore Types** ✅\n\n"
                           f"**Selected {len(self.selected_ores)} ore types:**\n"
                           f"{', '.join(sorted(ore_names))}",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="🔄 Next Step",
                value="Click 'Next' to proceed to Step 3",
                inline=False
            )
        else:
            embed = discord.Embed(
                title=f"⛏️ Mining Payroll - {self.parent_view.event_data['event_id']}",
                description=f"**Step 1 of 5: Event Selected** ✅\n"
                           f"**Step 2 of 5: Select Ore Types** ⏳\n\n"
                           f"Select which ore types were collected during this mining session.",
                color=discord.Color.blue()
            )
        
        # Force update the view to refresh button states
        try:
            await interaction.response.edit_message(embed=embed, view=self.parent_view)
        except:
            await interaction.response.defer()


class NextToQuantitiesButton(ui.Button):
    """Button to proceed to Step 3: Ore Quantities."""
    
    def __init__(self, event_data, processor, calculator, selected_ores, parent_view):
        super().__init__(
            label="Next",
            style=discord.ButtonStyle.primary,
            emoji="📊"
        )
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.selected_ores = selected_ores
        self.parent_view = parent_view
    
    async def callback(self, interaction: discord.Interaction):
        if not self.selected_ores:
            await interaction.response.send_message(
                "❌ Please select at least one ore type before proceeding.",
                ephemeral=True
            )
            return
        
        # Move to Step 3: Quantity Entry
        view = OreQuantityView(self.event_data, self.processor, self.calculator, self.selected_ores)
        
        # Create ore names list for display
        all_ores = {
            'AGRI': 'Agricium', 'ALUM': 'Aluminum', 'BERY': 'Beryl', 'BEXA': 'Bexalite',
            'BORA': 'Borase', 'COPP': 'Copper', 'DIAM': 'Diamond', 'GOLD': 'Gold',
            'HADA': 'Hadanite', 'HEPH': 'Hephaestanite', 'INRT': 'Inert Materials',
            'LARA': 'Laranite', 'QUAN': 'Quantanium', 'TARA': 'Taranite', 
            'TITA': 'Titanium', 'TUNG': 'Tungsten'
        }
        
        ore_names = []
        for code in sorted(self.selected_ores):
            ore_names.append(all_ores.get(code, code))
        
        embed = discord.Embed(
            title=f"⛏️ Mining Payroll - {self.event_data['event_id']}",
            description=f"**Step 1 of 5: Event Selected** ✅\n"
                       f"**Step 2 of 5: Select Ore Types** ✅\n"
                       f"**Step 3 of 5: Enter Quantities** ⏳\n\n"
                       f"Enter ore quantities and review UEX pricing for each selected ore type.",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📦 Selected Ores",
            value=f"{', '.join(ore_names)} ({len(ore_names)} types)",
            inline=False
        )
        
        embed.add_field(
            name="🔄 Instructions",
            value="1. Click 'Enter Ore Quantities' below\n"
                  "2. Review UEX prices and adjust quantities as needed\n"
                  "3. Submit to proceed to participant selection",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=view)


class OreQuantityView(ui.View):
    """Step 3: Enter quantities for selected ores."""
    
    def __init__(self, event_data, processor, calculator, selected_ores):
        super().__init__(timeout=600)
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.selected_ores = selected_ores
        
        # Add enter quantities button
        self.add_item(EnterQuantitiesButton(event_data, processor, calculator, selected_ores))
        
        # Add back button
        self.add_item(BackToOreSelectionButton(event_data, processor, calculator))
        
        # Add cancel button
        self.add_item(CancelButton())


class EnterQuantitiesButton(ui.Button):
    """Button to open quantity entry modal."""
    
    def __init__(self, event_data, processor, calculator, selected_ores):
        super().__init__(
            label="Enter Ore Quantities",
            style=discord.ButtonStyle.primary,
            emoji="📊"
        )
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.selected_ores = selected_ores
    
    async def callback(self, interaction: discord.Interaction):
        try:
            # Debug info
            print(f"🔍 Selected ores: {self.selected_ores}")
            print(f"🔍 Event data: {self.event_data.get('event_id', 'Unknown')}")
            
            if not self.selected_ores:
                await interaction.response.send_message(
                    "❌ No ores selected. Please go back and select ore types first.", 
                    ephemeral=True
                )
                return
            
            # Open modal for quantity entry
            modal = OreQuantityModal(self.event_data, self.processor, self.calculator, self.selected_ores)
            await interaction.response.send_modal(modal)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error opening quantity modal: {str(e)}\nSelected ores: {self.selected_ores}", 
                ephemeral=True
            )


class BackToOreSelectionButton(ui.Button):
    """Button to go back to Step 2."""
    
    def __init__(self, event_data, processor, calculator):
        super().__init__(
            label="← Back: Change Ore Selection",
            style=discord.ButtonStyle.secondary,
            emoji="⬅️"
        )
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
    
    async def callback(self, interaction: discord.Interaction):
        # Go back to Step 3
        view = ImprovedOreSelectionView(self.event_data, self.processor, self.calculator)
        
        embed = discord.Embed(
            title=f"⛏️ Mining Payroll - {self.event_data['event_id']}",
            description=f"**Step 1 of 5: Event Selected** ✅\n"
                       f"**Step 2 of 5: Select Ore Types** ⏳\n\n"
                       f"Select which ore types were collected during this mining session.",
            color=discord.Color.blue()
        )
        
        await interaction.response.edit_message(embed=embed, view=view)


class OreQuantityModal(ui.Modal):
    """Modal for entering ore quantities (Step 3)."""
    
    def __init__(self, event_data, processor, calculator, selected_ores):
        super().__init__(title=f'Ore Quantities & Pricing - {event_data["event_id"]}')
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.selected_ores = selected_ores
        
        # Create input fields for selected ores (no 5-field limit!)
        all_ores = {
            'AGRI': 'Agricium', 'ALUM': 'Aluminum', 'BERY': 'Beryl', 'BEXA': 'Bexalite',
            'BORA': 'Borase', 'COPP': 'Copper', 'DIAM': 'Diamond', 'GOLD': 'Gold',
            'HADA': 'Hadanite', 'HEPH': 'Hephaestanite', 'INRT': 'Inert Materials',
            'LARA': 'Laranite', 'QUAN': 'Quantanium', 'TARA': 'Taranite', 
            'TITA': 'Titanium', 'TUNG': 'Tungsten'
        }
        
        self.ore_inputs = {}
        sorted_selected = sorted(selected_ores)
        
        # Add input fields for up to 5 ores (Discord modal limit)
        # If more than 5, we'll need to handle in batches
        for i, ore_code in enumerate(sorted_selected[:5]):
            ore_name = all_ores.get(ore_code, ore_code)
            
            ore_input = ui.TextInput(
                label=f'{ore_name} Quantity (SCU)',
                placeholder=f'Enter SCU amount (UEX pricing shown next)',
                required=True,
                max_length=10
            )
            
            self.ore_inputs[ore_code] = ore_input
            self.add_item(ore_input)
        
        # If more than 5 ores selected, show note
        if len(selected_ores) > 5:
            self.remaining_ores = sorted_selected[5:]
        else:
            self.remaining_ores = []
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            # Parse entered quantities
            ore_quantities = {}
            for ore_code, input_field in self.ore_inputs.items():
                try:
                    quantity = float(input_field.value.strip())
                    if quantity < 0:
                        await interaction.followup.send(
                            f"❌ Quantity for {ore_code} must be 0 or greater.",
                            ephemeral=True
                        )
                        return
                    ore_quantities[ore_code] = quantity
                except ValueError:
                    await interaction.followup.send(
                        f"❌ Invalid quantity for {ore_code}: '{input_field.value}'",
                        ephemeral=True
                    )
                    return
            
            # If there are remaining ores, show second modal
            if self.remaining_ores:
                modal = OreQuantityModal2(
                    self.event_data, self.processor, self.calculator, 
                    self.remaining_ores, ore_quantities
                )
                await interaction.followup.send_modal(modal)
                return
            
            # All quantities collected, move to Step 3: Price Review
            try:
                # Get UEX prices for the selected ores
                prices = await self.processor.get_current_prices()
                
                # Calculate total value to get breakdown with UEX prices
                total_value, breakdown = await self.processor.calculate_total_value(ore_quantities, prices)
                
                # Create pricing modal with title "Per SCU Price" and UEX prices pre-filled
                modal = OrePricingModal(
                    self.event_data, self.processor, self.calculator, 
                    ore_quantities, breakdown
                )
                await interaction.response.send_modal(modal)
                
            except Exception as e:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ Error Loading UEX Pricing",
                        description=f"Failed to load UEX pricing: {str(e)}",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
            
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error Processing Quantities",
                    description=f"An error occurred: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
    
    async def _proceed_to_participants(self, interaction, ore_quantities):
        """Move to Step 4: Participant Selection."""
        # Get event participants
        participants = await self.calculator.get_event_participants(self.event_data['event_id'])
        
        if not participants:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ No Participants Found",
                    description="No participants found for this event.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return
        
        view = ParticipantSelectionView(
            self.event_data, self.processor, self.calculator, 
            ore_quantities, participants
        )
        
        embed = discord.Embed(
            title=f"⛏️ Mining Payroll - {self.event_data['event_id']}",
            description=f"**Step 1 of 5: Event Selected** ✅\n"
                       f"**Step 2 of 5: Select Ore Types** ✅\n"
                       f"**Step 3 of 5: Enter Quantities** ✅\n"
                       f"**Step 5 of 5: Participant Selection** ⏳\n\n"
                       f"Select which participants want to donate their share.",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="👥 Event Participants",
            value=f"Found {len(participants)} participants",
            inline=True
        )
        
        embed.add_field(
            name="💰 Donation Options",
            value="Check boxes for participants who want to donate their share to others",
            inline=True
        )
        
        await interaction.followup.edit_message(
            interaction.message.id,
            embed=embed,
            view=view
        )


class OreQuantityModal2(ui.Modal):
    """Second modal for remaining ores if more than 5 selected."""
    
    def __init__(self, event_data, processor, calculator, remaining_ores, first_batch_quantities):
        super().__init__(title=f'More Ore Quantities - {event_data["event_id"]}')
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.remaining_ores = remaining_ores
        self.first_batch_quantities = first_batch_quantities
        
        all_ores = {
            'AGRI': 'Agricium', 'ALUM': 'Aluminum', 'BERY': 'Beryl', 'BEXA': 'Bexalite',
            'BORA': 'Borase', 'COPP': 'Copper', 'DIAM': 'Diamond', 'GOLD': 'Gold',
            'HADA': 'Hadanite', 'HEPH': 'Hephaestanite', 'INRT': 'Inert Materials',
            'LARA': 'Laranite', 'QUAN': 'Quantanium', 'TARA': 'Taranite', 
            'TITA': 'Titanium', 'TUNG': 'Tungsten'
        }
        
        self.ore_inputs = {}
        
        # Add input fields for remaining ores (up to 5 more)
        for i, ore_code in enumerate(remaining_ores[:5]):
            ore_name = all_ores.get(ore_code, ore_code)
            
            ore_input = ui.TextInput(
                label=f'{ore_name} (SCU)',
                placeholder=f'Enter SCU amount for {ore_name}',
                required=True,
                max_length=10
            )
            
            self.ore_inputs[ore_code] = ore_input
            self.add_item(ore_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            # Parse entered quantities and combine with first batch
            all_ore_quantities = self.first_batch_quantities.copy()
            
            for ore_code, input_field in self.ore_inputs.items():
                try:
                    quantity = float(input_field.value.strip())
                    if quantity < 0:
                        await interaction.followup.send(
                            f"❌ Quantity for {ore_code} must be 0 or greater.",
                            ephemeral=True
                        )
                        return
                    all_ore_quantities[ore_code] = quantity
                except ValueError:
                    await interaction.followup.send(
                        f"❌ Invalid quantity for {ore_code}: '{input_field.value}'",
                        ephemeral=True
                    )
                    return
            
            # Check if there are even more ores (highly unlikely but possible)
            if len(self.remaining_ores) > 5:
                # Would need OreQuantityModal3, but this is very edge case
                await interaction.followup.send(
                    "❌ Too many ore types selected. Please reduce selection or contact admin.",
                    ephemeral=True
                )
                return
            
            # Move to Step 4: Participant Selection
            await self._proceed_to_participants(interaction, all_ore_quantities)
            
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error Processing Quantities",
                    description=f"An error occurred: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
    
    async def _proceed_to_participants(self, interaction, ore_quantities):
        """Move to Step 4: Participant Selection."""
        # Get event participants
        participants = await self.calculator.get_event_participants(self.event_data['event_id'])
        
        if not participants:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ No Participants Found", 
                    description="No participants found for this event.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return
        
        view = ParticipantSelectionView(
            self.event_data, self.processor, self.calculator,
            ore_quantities, participants
        )
        
        embed = discord.Embed(
            title=f"⛏️ Mining Payroll - {self.event_data['event_id']}",
            description=f"**Step 1 of 5: Event Selected** ✅\n"
                       f"**Step 2 of 5: Select Ore Types** ✅\n"
                       f"**Step 3 of 5: Enter Quantities** ✅\n"
                       f"**Step 5 of 5: Participant Selection** ⏳\n\n"
                       f"Select which participants want to donate their share.",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="👥 Event Participants",
            value=f"Found {len(participants)} participants",
            inline=True
        )
        
        embed.add_field(
            name="💰 Donation Options", 
            value="Check boxes for participants who want to donate their share to others",
            inline=True
        )
        
        # Try to edit the original message
        try:
            original_message = interaction.message
            await original_message.edit(embed=embed, view=view)
        except:
            await interaction.followup.send(embed=embed, view=view)


class ParticipantSelectionView(ui.View):
    """Step 4: Select which participants want to donate their share."""
    
    def __init__(self, event_data, processor, calculator, ore_quantities, participants):
        super().__init__(timeout=600)
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.ore_quantities = ore_quantities
        self.participants = participants
        self.donors = set()  # Track who is donating
        
        # Add participant checkboxes (up to 25 per dropdown due to Discord limits)
        if len(participants) <= 25:
            self.add_item(ParticipantDonationSelector(participants, self.donors, self))
        else:
            # Split into multiple dropdowns if too many participants
            batch_size = 25
            for i in range(0, len(participants), batch_size):
                batch = participants[i:i+batch_size]
                batch_num = i // batch_size + 1
                self.add_item(ParticipantDonationSelector(batch, self.donors, self, f"Batch {batch_num}"))
        
        # Add proceed to price review button
        self.add_item(ProceedToPriceReviewButton(
            event_data, processor, calculator, ore_quantities, participants, self.donors
        ))
        
        # Add back button
        self.add_item(BackToQuantitiesButton(event_data, processor, calculator, ore_quantities.keys()))
        
        # Add cancel button
        self.add_item(CancelButton())


class ParticipantDonationSelector(ui.Select):
    """Dropdown for selecting participants who want to donate."""
    
    def __init__(self, participants, donors, parent_view, batch_label=""):
        self.participants = participants
        self.donors = donors
        self.parent_view = parent_view
        
        options = []
        for participant in participants:
            username = participant.get('username', 'Unknown User')
            participation_time = participant.get('participation_minutes', 0)
            
            options.append(discord.SelectOption(
                label=f"{username} ({participation_time}min)",
                description=f"Select if {username} wants to donate their share",
                value=str(participant.get('user_id', username)),
                emoji="💝"
            ))
        
        placeholder = f"Select donors{f' - {batch_label}' if batch_label else ''}..."
        
        super().__init__(
            placeholder=placeholder,
            options=options,
            min_values=0,
            max_values=len(options)
        )
    
    async def callback(self, interaction: discord.Interaction):
        # Update donors set with current selections
        for participant in self.participants:
            user_id = str(participant.get('user_id', participant.get('username', '')))
            if user_id in self.values:
                self.donors.add(user_id)
            else:
                self.donors.discard(user_id)
        
        # Show feedback
        if self.values:
            donor_names = []
            for participant in self.participants:
                user_id = str(participant.get('user_id', participant.get('username', '')))
                if user_id in self.values:
                    donor_names.append(participant.get('username', 'Unknown'))
            
            await interaction.response.send_message(
                f"💝 **Donation Selection Updated**\n"
                f"**Donors:** {', '.join(donor_names)}\n"
                f"**Total donors:** {len(self.donors)} of {len(self.parent_view.participants)} participants\n\n"
                f"💡 Donated shares will be redistributed to non-donors based on participation time.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "⭕ Cleared donation selections from this group.",
                ephemeral=True
            )


class ProceedToPriceReviewButton(ui.Button):
    """Button to proceed to Step 5: Price Review."""
    
    def __init__(self, event_data, processor, calculator, ore_quantities, participants, donors):
        super().__init__(
            label="Next: Review Prices →",
            style=discord.ButtonStyle.primary,
            emoji="💰"
        )
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.ore_quantities = ore_quantities
        self.participants = participants
        self.donors = donors
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            # Get current ore prices
            prices = await self.processor.get_current_prices()
            if not prices:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ Price Data Unavailable",
                        description="Could not fetch ore prices from UEX Corp API or cache. Please try again later.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return
            
            # Calculate total value
            total_value, breakdown = await self.processor.calculate_total_value(self.ore_quantities, prices)
            
            if total_value <= 0:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ No Valid Ore Values",
                        description="Could not calculate value for any of the entered ores.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return
            
            # Move to Step 5: Price Review
            view = PriceReviewView(
                self.event_data, self.processor, self.calculator,
                self.ore_quantities, self.participants, self.donors,
                prices, total_value, breakdown
            )
            
            embed = discord.Embed(
                title=f"⛏️ Mining Payroll - {self.event_data['event_id']}",
                description=f"**Step 1 of 5: Event Selected** ✅\n"
                           f"**Step 2 of 5: Select Ore Types** ✅\n"
                           f"**Step 3 of 5: Enter Quantities** ✅\n"
                           f"**Step 5 of 5: Participant Selection** ✅\n"
                           f"**Step 5 of 5: Review & Calculate** ⏳\n\n"
                           f"Review prices and finalize payroll calculation.",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="💰 Total Value",
                value=f"{total_value:,.2f} aUEC",
                inline=True
            )
            
            embed.add_field(
                name="👥 Participants",
                value=f"{len(self.participants)} total\n{len(self.donors)} donors",
                inline=True
            )
            
            embed.add_field(
                name="📊 Ore Types",
                value=f"{len(self.ore_quantities)} types",
                inline=True
            )
            
            await interaction.edit_original_response(embed=embed, view=view)
            
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error Loading Price Data",
                    description=f"An error occurred: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )


class BackToQuantitiesButton(ui.Button):
    """Button to go back to Step 3: Quantities."""
    
    def __init__(self, event_data, processor, calculator, selected_ores):
        super().__init__(
            label="← Back: Change Quantities",
            style=discord.ButtonStyle.secondary,
            emoji="⬅️"
        )
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.selected_ores = selected_ores
    
    async def callback(self, interaction: discord.Interaction):
        # Go back to Step 3
        view = OreQuantityView(self.event_data, self.processor, self.calculator, self.selected_ores)
        
        # Create ore names list for display
        all_ores = {
            'AGRI': 'Agricium', 'ALUM': 'Aluminum', 'BERY': 'Beryl', 'BEXA': 'Bexalite',
            'BORA': 'Borase', 'COPP': 'Copper', 'DIAM': 'Diamond', 'GOLD': 'Gold',
            'HADA': 'Hadanite', 'HEPH': 'Hephaestanite', 'INRT': 'Inert Materials',
            'LARA': 'Laranite', 'QUAN': 'Quantanium', 'TARA': 'Taranite', 
            'TITA': 'Titanium', 'TUNG': 'Tungsten'
        }
        
        ore_names = []
        for code in sorted(self.selected_ores):
            ore_names.append(all_ores.get(code, code))
        
        embed = discord.Embed(
            title=f"⛏️ Mining Payroll - {self.event_data['event_id']}",
            description=f"**Step 1 of 5: Event Selected** ✅\n"
                       f"**Step 2 of 5: Select Ore Types** ✅\n"
                       f"**Step 3 of 5: Enter Quantities** ⏳\n\n"
                       f"Enter ore quantities and review UEX pricing for each selected ore type.",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📦 Selected Ores",
            value=f"{', '.join(ore_names)} ({len(ore_names)} types)",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=view)


class PriceReviewView(ui.View):
    """Step 5: Review prices and calculate final payroll."""
    
    def __init__(self, event_data, processor, calculator, ore_quantities, participants, donors, prices, total_value, breakdown):
        super().__init__(timeout=600)
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.ore_quantities = ore_quantities
        self.participants = participants
        self.donors = donors
        self.prices = prices
        self.total_value = total_value
        self.breakdown = breakdown
        
        # Add edit prices button
        self.add_item(EditPricesInlineButton(
            event_data, processor, calculator, ore_quantities, participants, donors,
            prices, total_value, breakdown, self
        ))
        
        # Add final calculate button
        self.add_item(FinalCalculateButton(
            event_data, processor, calculator, ore_quantities, participants, donors,
            prices, total_value, breakdown
        ))
        
        # Add back button
        self.add_item(BackToParticipantsButton(
            event_data, processor, calculator, ore_quantities, participants
        ))
        
        # Add cancel button
        self.add_item(CancelButton())


class EditPricesInlineButton(ui.Button):
    """Button to edit ore prices inline."""
    
    def __init__(self, event_data, processor, calculator, ore_quantities, participants, donors, prices, total_value, breakdown, parent_view):
        super().__init__(
            label="Edit Prices",
            style=discord.ButtonStyle.secondary,
            emoji="✏️"
        )
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.ore_quantities = ore_quantities
        self.participants = participants
        self.donors = donors
        self.prices = prices
        self.total_value = total_value
        self.breakdown = breakdown
        self.parent_view = parent_view
    
    async def callback(self, interaction: discord.Interaction):
        # Create price editing modal
        modal = InlinePriceEditModal(
            self.event_data, self.processor, self.calculator,
            self.ore_quantities, self.participants, self.donors,
            self.prices, self.breakdown, self.parent_view
        )
        await interaction.response.send_modal(modal)


class InlinePriceEditModal(ui.Modal):
    """Modal for editing ore prices in Step 5."""
    
    def __init__(self, event_data, processor, calculator, ore_quantities, participants, donors, prices, breakdown, parent_view):
        super().__init__(title=f'Edit Prices - {event_data["event_id"]}')
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.ore_quantities = ore_quantities
        self.participants = participants
        self.donors = donors
        self.prices = prices
        self.breakdown = breakdown
        self.parent_view = parent_view
        
        self.price_inputs = {}
        
        # Add price inputs for up to 5 ores
        ore_count = 0
        for ore_code, quantity in list(ore_quantities.items())[:5]:
            if quantity > 0:  # Only show ores with quantities
                all_ores = {
                    'AGRI': 'Agricium', 'ALUM': 'Aluminum', 'BERY': 'Beryl', 'BEXA': 'Bexalite',
                    'BORA': 'Borase', 'COPP': 'Copper', 'DIAM': 'Diamond', 'GOLD': 'Gold',
                    'HADA': 'Hadanite', 'HEPH': 'Hephaestanite', 'INRT': 'Inert Materials',
                    'LARA': 'Laranite', 'QUAN': 'Quantanium', 'TARA': 'Taranite', 
                    'TITA': 'Titanium', 'TUNG': 'Tungsten'
                }
                
                ore_name = all_ores.get(ore_code, ore_code)
                current_price = breakdown.get(ore_code.upper(), {}).get('price_per_scu', 0)
                
                price_input = ui.TextInput(
                    label=f'{ore_name} Price (per SCU)',
                    placeholder=f'Current UEX price: {current_price:,.0f} aUEC',
                    default=str(int(current_price)) if current_price > 0 else '',
                    required=True,
                    max_length=10
                )
                
                self.price_inputs[ore_code] = price_input
                self.add_item(price_input)
                ore_count += 1
                
                if ore_count >= 5:
                    break
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            # Parse new prices
            updated_prices = {}
            for ore_code, input_field in self.price_inputs.items():
                try:
                    new_price = float(input_field.value.strip())
                    if new_price < 0:
                        await interaction.followup.send(
                            f"❌ Price for {ore_code} must be 0 or greater.",
                            ephemeral=True
                        )
                        return
                    updated_prices[ore_code] = new_price
                except ValueError:
                    await interaction.followup.send(
                        f"❌ Invalid price for {ore_code}: '{input_field.value}'",
                        ephemeral=True
                    )
                    return
            
            # Recalculate total value with new prices
            new_breakdown = {}
            new_total_value = 0
            
            for ore_code, quantity in self.ore_quantities.items():
                if quantity > 0:
                    if ore_code in updated_prices:
                        price_per_scu = updated_prices[ore_code]
                    else:
                        price_per_scu = self.breakdown.get(ore_code.upper(), {}).get('price_per_scu', 0)
                    
                    total_ore_value = quantity * price_per_scu
                    new_breakdown[ore_code.upper()] = {
                        'scu_amount': quantity,
                        'price_per_scu': price_per_scu,
                        'total_value': total_ore_value
                    }
                    new_total_value += total_ore_value
            
            # Update parent view
            self.parent_view.breakdown = new_breakdown
            self.parent_view.total_value = new_total_value
            
            # Update all buttons with new values
            for item in self.parent_view.children:
                if hasattr(item, 'total_value'):
                    item.total_value = new_total_value
                    item.breakdown = new_breakdown
            
            # Create updated embed
            embed = discord.Embed(
                title=f"⛏️ Mining Payroll - {self.event_data['event_id']} (Prices Updated)",
                description=f"**Step 1 of 5: Event Selected** ✅\n"
                           f"**Step 2 of 5: Select Ore Types** ✅\n"
                           f"**Step 3 of 5: Enter Quantities** ✅\n"
                           f"**Step 5 of 5: Participant Selection** ✅\n"
                           f"**Step 5 of 5: Review & Calculate** ⏳\n\n"
                           f"Prices updated! Ready to calculate final payroll.",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="💰 Updated Total Value",
                value=f"{new_total_value:,.2f} aUEC",
                inline=True
            )
            
            embed.add_field(
                name="👥 Participants",
                value=f"{len(self.participants)} total\n{len(self.donors)} donors",
                inline=True
            )
            
            # Show price changes
            price_changes = []
            for ore_code, new_price in updated_prices.items():
                all_ores = {
                    'AGRI': 'Agricium', 'ALUM': 'Aluminum', 'BERY': 'Beryl', 'BEXA': 'Bexalite',
                    'BORA': 'Borase', 'COPP': 'Copper', 'DIAM': 'Diamond', 'GOLD': 'Gold',
                    'HADA': 'Hadanite', 'HEPH': 'Hephaestanite', 'INRT': 'Inert Materials',
                    'LARA': 'Laranite', 'QUAN': 'Quantanium', 'TARA': 'Taranite', 
                    'TITA': 'Titanium', 'TUNG': 'Tungsten'
                }
                ore_name = all_ores.get(ore_code, ore_code)
                price_changes.append(f"**{ore_name}:** {new_price:,.0f} aUEC ✏️")
            
            if price_changes:
                embed.add_field(
                    name="✏️ Price Updates",
                    value="\n".join(price_changes[:5]),
                    inline=False
                )
            
            await interaction.edit_original_response(embed=embed, view=self.parent_view)
            
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error Updating Prices",
                    description=f"An error occurred: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )


class FinalCalculateButton(ui.Button):
    """Button to execute final payroll calculation."""
    
    def __init__(self, event_data, processor, calculator, ore_quantities, participants, donors, prices, total_value, breakdown):
        super().__init__(
            label="Calculate Final Payroll",
            style=discord.ButtonStyle.success,
            emoji="✅"
        )
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.ore_quantities = ore_quantities
        self.participants = participants
        self.donors = donors
        self.prices = prices
        self.total_value = total_value
        self.breakdown = breakdown
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            # Calculate final payroll with donations
            result = await self.calculator.calculate_payroll(
                event_id=self.event_data['event_id'],
                total_value_auec=self.total_value,
                collection_data={
                    'ores': self.ore_quantities,
                    'total_scu': sum(self.ore_quantities.values()),
                    'breakdown': self.breakdown
                },
                price_data=self.prices,
                calculated_by_id=interaction.user.id,
                calculated_by_name=interaction.user.display_name,
                donation_data={
                    'donors': list(self.donors),
                    'donation_percentage': 0  # Individual donation system, not percentage
                }
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
            embed = discord.Embed(
                title="✅ Payroll Calculation Complete!",
                description=f"**Event:** {self.event_data['event_id']}\n"
                           f"**Total Value:** {result['total_value_auec']:,.2f} aUEC\n"
                           f"**Participants:** {result['total_participants']}",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="📊 Distribution Summary",
                value=f"**Session Duration:** {result.get('total_minutes', 'Unknown')} minutes\n"
                      f"**Donors:** {len(self.donors)} participants\n"
                      f"**Payroll ID:** `{result.get('payroll_id', 'Unknown')}`",
                inline=False
            )
            
            # Show top payouts
            if result.get('payouts'):
                top_payouts = sorted(result['payouts'], key=lambda x: x.get('final_payout_auec', 0), reverse=True)[:5]
                payout_text = []
                for payout in top_payouts:
                    donation_marker = " 💝" if str(payout.get('user_id', '')) in self.donors else ""
                    payout_text.append(
                        f"**{payout.get('username', 'Unknown')}:** {payout.get('final_payout_auec', 0):,.0f} aUEC "
                        f"({payout.get('participation_minutes', 0)}min){donation_marker}"
                    )
                
                embed.add_field(
                    name="🏆 Top Payouts",
                    value="\n".join(payout_text),
                    inline=False
                )
            
            embed.set_footer(text=f"Calculated by {interaction.user.display_name}")
            
            # Disable all buttons in the view
            for item in self.view.children:
                item.disabled = True
            
            await interaction.edit_original_response(embed=embed, view=self.view)
            
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error Calculating Payroll",
                    description=f"An unexpected error occurred: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )


class BackToParticipantsButton(ui.Button):
    """Button to go back to Step 4: Participant selection."""
    
    def __init__(self, event_data, processor, calculator, ore_quantities, participants):
        super().__init__(
            label="← Back: Change Participants",
            style=discord.ButtonStyle.secondary,
            emoji="⬅️"
        )
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.ore_quantities = ore_quantities
        self.participants = participants
    
    async def callback(self, interaction: discord.Interaction):
        # Go back to Step 4
        view = ParticipantSelectionView(
            self.event_data, self.processor, self.calculator,
            self.ore_quantities, self.participants
        )
        
        embed = discord.Embed(
            title=f"⛏️ Mining Payroll - {self.event_data['event_id']}",
            description=f"**Step 1 of 5: Event Selected** ✅\n"
                       f"**Step 2 of 5: Select Ore Types** ✅\n"
                       f"**Step 3 of 5: Enter Quantities** ✅\n"
                       f"**Step 5 of 5: Participant Selection** ⏳\n\n"
                       f"Select which participants want to donate their share.",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="👥 Event Participants",
            value=f"Found {len(self.participants)} participants",
            inline=True
        )
        
        embed.add_field(
            name="💰 Donation Options",
            value="Check boxes for participants who want to donate their share to others",
            inline=True
        )
        
        await interaction.response.edit_message(embed=embed, view=view)


class CancelButton(ui.Button):
    """Universal cancel button."""
    
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


class SalvageCollectionModal(ui.Modal):
    """Modal for inputting salvage collections."""
    
    def __init__(self, event_data: Dict, processor, calculator):
        super().__init__(title=f'Salvage Payroll - {event_data["event_id"]}')
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        
        # Placeholder for salvage inputs
        self.components = ui.TextInput(
            label='Components Collected',
            placeholder='Component A: 5, Component B: 3',
            required=False,
            style=discord.TextStyle.paragraph,
            max_length=500
        )
        
        self.materials = ui.TextInput(
            label='Raw Materials',
            placeholder='Material type and quantities',
            required=False,
            max_length=100
        )
        
        self.add_item(self.components)
        self.add_item(self.materials)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🔧 Salvage Module Coming Soon",
                description="Salvage payroll calculations will be available when the salvage module is implemented.",
                color=discord.Color.blue()
            ),
            ephemeral=True
        )


class OrePricingModal(ui.Modal):
    """Modal for reviewing and adjusting UEX ore prices (Step 3)."""
    
    def __init__(self, event_data, processor, calculator, ore_quantities, breakdown):
        super().__init__(title='Per SCU Price')
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.ore_quantities = ore_quantities
        self.breakdown = breakdown
        
        # Create price input fields for each ore with UEX prices pre-filled
        all_ores = {
            'AGRI': 'Agricium', 'ALUM': 'Aluminum', 'BERY': 'Beryl', 'BEXA': 'Bexalite',
            'BORA': 'Borase', 'COPP': 'Copper', 'DIAM': 'Diamond', 'GOLD': 'Gold',
            'HADA': 'Hadanite', 'HEPH': 'Hephaestanite', 'INRT': 'Inert Materials',
            'LARA': 'Laranite', 'QUAN': 'Quantanium', 'TARA': 'Taranite', 
            'TITA': 'Titanium', 'TUNG': 'Tungsten'
        }
        
        self.price_inputs = {}
        
        # Add price inputs for up to 5 ores (Discord modal limit)
        ore_count = 0
        for ore_code, quantity in list(ore_quantities.items())[:5]:
            if quantity > 0:  # Only show ores with quantities
                ore_name = all_ores.get(ore_code, ore_code)
                current_price = breakdown.get(ore_code.upper(), {}).get('price_per_scu', 0)
                
                price_input = ui.TextInput(
                    label=f'{ore_name} Price (per SCU)',
                    placeholder=f'Current UEX price: {current_price:,.0f} aUEC',
                    default=str(int(current_price)) if current_price > 0 else '',
                    required=True,
                    max_length=10
                )
                
                self.price_inputs[ore_code] = price_input
                self.add_item(price_input)
                ore_count += 1
                
                if ore_count >= 5:
                    break
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            # Parse entered prices
            updated_prices = {}
            for ore_code, input_field in self.price_inputs.items():
                try:
                    price = float(input_field.value.strip())
                    if price < 0:
                        await interaction.followup.send(
                            f"❌ Price for {ore_code} must be 0 or greater.",
                            ephemeral=True
                        )
                        return
                    updated_prices[ore_code] = price
                except ValueError:
                    await interaction.followup.send(
                        f"❌ Invalid price for {ore_code}: '{input_field.value}'",
                        ephemeral=True
                    )
                    return
            
            # Now proceed to Step 4: Participant Selection with updated prices
            await self._proceed_to_participants(interaction, updated_prices)
            
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error Processing Prices",
                    description=f"An error occurred: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
    
    async def _proceed_to_participants(self, interaction, updated_prices):
        """Move to Step 4: Participant Selection with pricing confirmed."""
        # Get event participants
        participants = await self.calculator.get_event_participants(self.event_data['event_id'])
        
        if not participants:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ No Participants Found",
                    description="No participants found for this event.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return
        
        # Create new view for participant selection with confirmed pricing
        view = ParticipantSelectionView(
            self.event_data, self.processor, self.calculator, 
            self.ore_quantities, participants, updated_prices
        )
        
        embed = discord.Embed(
            title=f"⛏️ Mining Payroll - {self.event_data['event_id']}",
            description=f"**Step 1 of 5: Event Selected** ✅\n"
                       f"**Step 2 of 5: Select Ore Types** ✅\n"
                       f"**Step 3 of 5: Enter Quantities** ✅\n"
                       f"**Step 4 of 5: Review Pricing** ✅\n"
                       f"**Step 5 of 5: Participant Selection** ⏳\n\n"
                       f"Select participants for payroll calculation.",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="👥 Event Participants",
            value=f"Found {len(participants)} participants",
            inline=True
        )
        
        await interaction.followup.edit_message(
            interaction.message.id,
            embed=embed,
            view=view
        )


# =====================================================
# DIRECT QUANTITY ENTRY FLOW (User's Preferred Flow)
# =====================================================

class DirectQuantityEntryView(ui.View):
    """Step 2: Direct quantity entry view - skips ore selection step."""
    
    def __init__(self, event_data, processor, calculator):
        super().__init__(timeout=300)
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        
        # Add quantity entry button
        self.add_item(DirectQuantityEntryButton(event_data, processor, calculator))
        
        # Add cancel button
        self.add_item(CancelButton())


class DirectQuantityEntryButton(ui.Button):
    """Button to open quantity entry modal for common ores."""
    
    def __init__(self, event_data, processor, calculator):
        super().__init__(
            label="Enter Ore Quantities",
            style=discord.ButtonStyle.primary,
            emoji="📊"
        )
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
    
    async def callback(self, interaction: discord.Interaction):
        try:
            # Open modal for quantity entry with common ores pre-populated
            modal = DirectOreQuantityModal(self.event_data, self.processor, self.calculator)
            await interaction.response.send_modal(modal)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error opening quantity modal: {str(e)}", 
                ephemeral=True
            )


class DirectOreQuantityModal(ui.Modal):
    """Modal for direct ore quantity entry - Step 2 as user requested."""
    
    def __init__(self, event_data, processor, calculator):
        super().__init__(title=f'Enter Ore Quantities - {event_data["event_id"]}')
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        
        # Pre-populate with most common mining ores (user can enter 0 for unused)
        common_ores = {
            'QUAN': 'Quantanium',
            'LARA': 'Laranite', 
            'AGRI': 'Agricium',
            'HADA': 'Hadanite',
            'BERY': 'Beryl'
        }
        
        self.ore_inputs = {}
        
        # Add input fields for common ores
        for ore_code, ore_name in common_ores.items():
            ore_input = ui.TextInput(
                label=f'{ore_name} (SCU)',
                placeholder=f'Enter SCU amount or 0 if not collected',
                required=False,
                max_length=10,
                default='0'
            )
            
            self.ore_inputs[ore_code] = ore_input
            self.add_item(ore_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            # Parse entered quantities
            ore_quantities = {}
            total_scu = 0
            
            for ore_code, input_field in self.ore_inputs.items():
                try:
                    quantity = float(input_field.value.strip()) if input_field.value.strip() else 0
                    if quantity < 0:
                        await interaction.followup.send(
                            f"❌ Quantity for {ore_code} cannot be negative.",
                            ephemeral=True
                        )
                        return
                    if quantity > 0:
                        ore_quantities[ore_code] = quantity
                        total_scu += quantity
                except ValueError:
                    await interaction.followup.send(
                        f"❌ Invalid quantity for {ore_code}: '{input_field.value}'",
                        ephemeral=True
                    )
                    return
            
            if total_scu == 0:
                await interaction.followup.send(
                    "❌ Please enter at least some ore quantities greater than 0.",
                    ephemeral=True
                )
                return
            
            # Get current ore prices (no loading message to avoid interaction conflicts)
            ore_prices = await self.processor.get_current_prices()
            if not ore_prices:
                await interaction.followup.send(
                    "❌ Unable to fetch ore prices. Please try again.",
                    ephemeral=True
                )
                return
            
            # Proceed to Step 3: UEX Pricing Review
            view = DirectPricingReviewView(
                self.event_data, self.processor, self.calculator, 
                ore_quantities, ore_prices
            )
            
            embed = discord.Embed(
                title=f"⛏️ Mining Payroll - {self.event_data['event_id']}",
                description=f"**Step 1 of 4: Event Selected** ✅\n"
                           f"**Step 2 of 4: Enter Quantities** ✅\n"
                           f"**Step 3 of 4: Review UEX Pricing** ⏳\n\n"
                           f"Review current UEX Corp ore prices.",
                color=discord.Color.blue()
            )
            
            await interaction.followup.edit_message(
                interaction.message.id,
                embed=embed,
                view=view
            )
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error processing quantities: {str(e)}",
                ephemeral=True
            )


class DirectPricingReviewView(ui.View):
    """Step 3: UEX pricing review view - user's preferred Step 3."""
    
    def __init__(self, event_data, processor, calculator, ore_quantities, ore_prices):
        super().__init__(timeout=300)
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.ore_quantities = ore_quantities
        self.ore_prices = ore_prices
        
        # Add UEX pricing review button
        self.add_item(DirectPricingButton(event_data, processor, calculator, ore_quantities, ore_prices))
        
        # Add back button
        self.add_item(BackToQuantitiesButton(event_data, processor, calculator))
        
        # Add cancel button
        self.add_item(CancelButton())


class DirectPricingButton(ui.Button):
    """Button to open UEX pricing review modal."""
    
    def __init__(self, event_data, processor, calculator, ore_quantities, ore_prices):
        super().__init__(
            label="Review UEX Prices",
            style=discord.ButtonStyle.primary,
            emoji="💰"
        )
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.ore_quantities = ore_quantities
        self.ore_prices = ore_prices
    
    async def callback(self, interaction: discord.Interaction):
        try:
            # Validate that we have prices before opening modal
            if not self.ore_prices:
                await interaction.response.send_message(
                    "❌ Error Loading UEX Pricing\nFailed to load UEX pricing: No price data available. Please try again.",
                    ephemeral=True
                )
                return
                
            # Check if any of our collected ores have prices
            has_prices = any(
                self.ore_prices.get(ore_code, {}).get('price', 0) > 0 
                for ore_code in self.ore_quantities.keys()
            )
            
            if not has_prices:
                await interaction.response.send_message(
                    "❌ Error Loading UEX Pricing\nFailed to load UEX pricing: No prices found for collected ores. Please try again.",
                    ephemeral=True
                )
                return
            
            # Show UEX pricing modal with title as requested by user
            modal = DirectUEXPricingModal(
                self.event_data, self.processor, self.calculator,
                self.ore_quantities, self.ore_prices
            )
            await interaction.response.send_modal(modal)
        except Exception as e:
            # Check if interaction was already responded to
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"❌ Error Loading UEX Pricing\nFailed to load UEX pricing: {str(e)}", 
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"❌ Error Loading UEX Pricing\nFailed to load UEX pricing: {str(e)}", 
                    ephemeral=True
                )


class DirectUEXPricingModal(ui.Modal):
    """UEX pricing review modal - titled 'Per SCU Price' as user requested."""
    
    def __init__(self, event_data, processor, calculator, ore_quantities, ore_prices):
        super().__init__(title='Per SCU Price')  # User's requested title
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.ore_quantities = ore_quantities
        self.ore_prices = ore_prices
        
        # Show current UEX prices for collected ores
        self.price_inputs = {}
        
        for ore_code, quantity in ore_quantities.items():
            if quantity > 0:
                ore_name = self.get_ore_name(ore_code)
                # Get price safely with fallback
                price_data = ore_prices.get(ore_code, {})
                if isinstance(price_data, dict):
                    current_price = price_data.get('price', 0)
                else:
                    current_price = 0
                
                price_input = ui.TextInput(
                    label=f'{ore_name} (aUEC/SCU)',
                    placeholder=f'Current UEX price: {current_price}' if current_price > 0 else 'Enter price per SCU',
                    required=True,
                    max_length=10,
                    default=str(current_price) if current_price > 0 else '0'
                )
                
                self.price_inputs[ore_code] = price_input
                self.add_item(price_input)
    
    def get_ore_name(self, ore_code):
        """Get full ore name from code."""
        ore_names = {
            'QUAN': 'Quantanium', 'LARA': 'Laranite', 'AGRI': 'Agricium',
            'HADA': 'Hadanite', 'BERY': 'Beryl', 'BEXA': 'Bexalite',
            'DIAM': 'Diamond', 'GOLD': 'Gold', 'TARA': 'Taranite',
            'TITA': 'Titanium', 'TUNG': 'Tungsten', 'ALUM': 'Aluminum',
            'COPP': 'Copper', 'INRT': 'Inert Materials', 'HEPH': 'Hephaestanite',
            'BORA': 'Borase'
        }
        return ore_names.get(ore_code, ore_code)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            # Parse updated prices
            updated_prices = {}
            for ore_code, input_field in self.price_inputs.items():
                try:
                    price = float(input_field.value.strip())
                    if price < 0:
                        await interaction.followup.send(
                            f"❌ Price for {ore_code} cannot be negative.",
                            ephemeral=True
                        )
                        return
                    updated_prices[ore_code] = {'price': price}
                except ValueError:
                    await interaction.followup.send(
                        f"❌ Invalid price for {ore_code}: '{input_field.value}'",
                        ephemeral=True
                    )
                    return
            
            # Get participants
            participants = await self.calculator.get_event_participants(self.event_data['event_id'])
            if not participants:
                await interaction.followup.send(
                    "❌ No participants found for this event.",
                    ephemeral=True
                )
                return
            
            # Proceed to Step 4: Participant Selection
            view = DirectParticipantSelectionView(
                self.event_data, self.processor, self.calculator,
                self.ore_quantities, participants, updated_prices
            )
            
            embed = discord.Embed(
                title=f"⛏️ Mining Payroll - {self.event_data['event_id']}",
                description=f"**Step 1 of 4: Event Selected** ✅\n"
                           f"**Step 2 of 4: Enter Quantities** ✅\n"
                           f"**Step 3 of 4: Review UEX Pricing** ✅\n"
                           f"**Step 4 of 4: Participant Selection** ⏳\n\n"
                           f"Select participants for payroll calculation.",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="👥 Event Participants",
                value=f"Found {len(participants)} participants",
                inline=True
            )
            
            await interaction.followup.edit_message(
                interaction.message.id,
                embed=embed,
                view=view
            )
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error processing pricing: {str(e)}",
                ephemeral=True
            )


class DirectParticipantSelectionView(ui.View):
    """Step 4: Final participant selection for direct flow."""
    
    def __init__(self, event_data, processor, calculator, ore_quantities, participants, ore_prices):
        super().__init__(timeout=300)
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.ore_quantities = ore_quantities
        self.participants = participants
        self.ore_prices = ore_prices
        
        # Add participant selection dropdown
        self.add_item(DirectParticipantSelector(
            event_data, processor, calculator, ore_quantities, participants, ore_prices
        ))
        
        # Add final calculation button
        self.add_item(DirectFinalCalculationButton(
            event_data, processor, calculator, ore_quantities, participants, ore_prices
        ))
        
        # Add cancel button
        self.add_item(CancelButton())


class DirectParticipantSelector(ui.Select):
    """Participant selection dropdown for direct flow."""
    
    def __init__(self, event_data, processor, calculator, ore_quantities, participants, ore_prices):
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.ore_quantities = ore_quantities
        self.participants = participants
        self.ore_prices = ore_prices
        
        # Create options for participants
        options = []
        for participant in participants[:25]:  # Discord limit
            username = participant['username']
            minutes = int(participant.get('total_minutes', 0))
            hours = minutes // 60
            mins = minutes % 60
            time_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
            
            options.append(discord.SelectOption(
                label=username,
                description=f"Participated for {time_str}",
                value=str(participant['user_id']),
                default=True  # Default all to selected
            ))
        
        super().__init__(
            placeholder="Select participants to include in payroll...",
            options=options,
            min_values=1,
            max_values=len(options)
        )
    
    async def callback(self, interaction: discord.Interaction):
        # Update view with selected participants
        await interaction.response.defer()


class DirectFinalCalculationButton(ui.Button):
    """Final calculation button for direct flow."""
    
    def __init__(self, event_data, processor, calculator, ore_quantities, participants, ore_prices):
        super().__init__(
            label="Calculate Final Payroll",
            style=discord.ButtonStyle.success,
            emoji="💰"
        )
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        self.ore_quantities = ore_quantities
        self.participants = participants
        self.ore_prices = ore_prices
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            # Calculate total value
            total_value, breakdown = await self.processor.calculate_total_value(
                self.ore_quantities, self.ore_prices
            )
            
            # Create final confirmation view
            from .views import PayrollConfirmationView
            view = PayrollConfirmationView(
                self.event_data, self.processor, self.calculator,
                self.ore_quantities, breakdown, total_value
            )
            
            embed = discord.Embed(
                title=f"⛏️ Mining Payroll - {self.event_data['event_id']} - READY",
                description=f"**All Steps Complete** ✅\n\n"
                           f"Ready to calculate final payroll.",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="💰 Total Value",
                value=f"{total_value:,.2f} aUEC",
                inline=True
            )
            
            embed.add_field(
                name="👥 Participants",
                value=f"{len(self.participants)} people",
                inline=True
            )
            
            await interaction.followup.edit_message(
                interaction.message.id,
                embed=embed,
                view=view
            )
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error calculating payroll: {str(e)}",
                ephemeral=True
            )


class BackToQuantitiesButton(ui.Button):
    """Button to go back to quantity entry."""
    
    def __init__(self, event_data, processor, calculator):
        super().__init__(
            label="← Back: Change Quantities",
            style=discord.ButtonStyle.secondary,
            emoji="⬅️"
        )
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
    
    async def callback(self, interaction: discord.Interaction):
        # Go back to Step 2: quantity entry
        view = DirectQuantityEntryView(self.event_data, self.processor, self.calculator)
        
        embed = discord.Embed(
            title=f"⛏️ Mining Payroll - {self.event_data['event_id']}",
            description=f"**Step 1 of 4: Event Selected** ✅\n"
                       f"**Step 2 of 4: Enter Quantities** ⏳\n\n"
                       f"Enter ore quantities collected during this mining session.",
            color=discord.Color.blue()
        )
        
        await interaction.response.edit_message(embed=embed, view=view)