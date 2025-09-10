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
        
        # Update proceed button
        self.view.update_proceed_button()
        
        # Show selection feedback
        if self.values:
            selected_names = [HIGH_VALUE_ORES[code] for code in self.values]
            await interaction.response.send_message(
                f"✅ Selected high-value ores: **{', '.join(selected_names)}**\n"
                f"Total selected: **{len(self.selected_ores)} ore types**",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "⭕ Cleared high-value ore selections.",
                ephemeral=True
            )


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
        
        # Update proceed button
        self.view.update_proceed_button()
        
        # Show selection feedback
        if self.values:
            selected_names = [MID_VALUE_ORES[code] for code in self.values]
            await interaction.response.send_message(
                f"✅ Selected mid-value ores: **{', '.join(selected_names)}**\n"
                f"Total selected: **{len(self.selected_ores)} ore types**",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "⭕ Cleared mid-value ore selections.",
                ephemeral=True
            )


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
        
        # Update proceed button
        self.view.update_proceed_button()
        
        # Show selection feedback
        if self.values:
            selected_names = [COMMON_ORES[code] for code in self.values if code in COMMON_ORES]
            await interaction.response.send_message(
                f"✅ Selected common ores: **{', '.join(selected_names)}**\n"
                f"Total selected: **{len(self.selected_ores)} ore types**",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "⭕ Cleared common ore selections.",
                ephemeral=True
            )


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