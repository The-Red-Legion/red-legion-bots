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

class MiningCollectionModal(ui.Modal):
    """Modal for inputting mining ore collections."""
    
    def __init__(self, event_data: Dict, processor, calculator):
        super().__init__(title=f'Mining Payroll - {event_data["event_id"]}')
        self.event_data = event_data
        self.processor = processor
        self.calculator = calculator
        
        # Create input fields for common ores
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
        
        self.laranite = ui.TextInput(
            label='Laranite (SCU)',
            placeholder='0.0', 
            default='0',
            required=False,
            max_length=10
        )
        
        self.agricium = ui.TextInput(
            label='Agricium (SCU)',
            placeholder='0.0',
            default='0', 
            required=False,
            max_length=10
        )
        
        self.other_ores = ui.TextInput(
            label='Other Ores (format: "Gold:5.2,Titanium:12.1")',
            placeholder='OreName:Amount,OreName:Amount',
            required=False,
            style=discord.TextStyle.paragraph,
            max_length=500
        )
        
        # Add all inputs to the modal
        self.add_item(self.quantainium)
        self.add_item(self.bexalite)
        self.add_item(self.laranite) 
        self.add_item(self.agricium)
        self.add_item(self.other_ores)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            # Parse ore collections
            ore_collections = {}
            
            # Parse main ore inputs
            main_ores = {
                'QUANTAINIUM': self.quantainium.value,
                'BEXALITE': self.bexalite.value,
                'LARANITE': self.laranite.value,
                'AGRICIUM': self.agricium.value
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
            
            # Parse other ores field
            if self.other_ores.value and self.other_ores.value.strip():
                try:
                    other_pairs = self.other_ores.value.strip().split(',')
                    for pair in other_pairs:
                        if ':' in pair:
                            ore_name, amount_str = pair.split(':', 1)
                            ore_name = ore_name.strip().upper()
                            amount = float(amount_str.strip())
                            if amount > 0:
                                ore_collections[ore_name] = amount
                except ValueError as e:
                    await interaction.followup.send(
                        f"❌ Error parsing other ores: {str(e)}\nFormat: 'OreName:Amount,OreName:Amount'",
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