"""
Sunday Mining Module for Red Legion Discord Bot

This module handles Sunday mining operations including:
- Voice participation tracking across 7 mining channels
- Ore collection reporting through Discord modals
- Automated payroll calculation using UEX API
- Mining session management and reporting

Commands:
- /redsundayminingstart: Start a Sunday mining session
- /redsundayminingstop: Stop the current mining session 
- /redpayroll: Calculate and display payroll for the last session
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Optional
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import (
    ORE_TYPES, 
    UEX_API_CONFIG
)
from config.channels import get_sunday_mining_channels
from handlers.voice_tracking import (
    add_tracked_channel, 
    remove_tracked_channel, 
    start_voice_tracking,
    stop_voice_tracking
)
from utils import can_manage_payroll

# Global state for Sunday mining sessions
current_session = {
    'active': False,
    'start_time': None,
    'event_id': None,
    'participants': {}  # {user_id: participation_data}
}


class ParticipantDonationView(discord.ui.View):
    """View for selecting participants who want to donate their earnings."""
    
    def __init__(self, participants_data, event_id, ore_prices):
        super().__init__(timeout=300)  # 5 minute timeout
        self.participants_data = participants_data
        self.event_id = event_id
        self.ore_prices = ore_prices
        self.donations = {}  # Track who's donating
        
        # Create checkboxes for each participant (up to 25 due to Discord limits)
        participant_list = list(participants_data.items())[:20]  # Limit for UI space
        
        if len(participant_list) <= 5:
            # Use buttons for small groups
            for member_id, data in participant_list:
                button = discord.ui.Button(
                    label=f"💰 {data['username'][:20]}",
                    style=discord.ButtonStyle.secondary,
                    custom_id=f"donate_{member_id}"
                )
                button.callback = self._create_toggle_callback(member_id)
                self.add_item(button)
        else:
            # Use select menu for larger groups
            options = []
            for member_id, data in participant_list:
                options.append(discord.SelectOption(
                    label=f"{data['username']}"[:100],
                    description=f"Mining time: {data['hours']:.1f}h - Click to toggle donation"[:100],
                    value=str(member_id),
                    emoji="💰"
                ))
            
            if options:
                self.participant_select = discord.ui.Select(
                    placeholder="Select participants who want to donate their earnings...",
                    options=options,
                    max_values=len(options),
                    min_values=0
                )
                self.participant_select.callback = self.participants_selected
                self.add_item(self.participant_select)
        
        # Continue to prices button
        continue_button = discord.ui.Button(
            label="Continue to Price Setup →",
            style=discord.ButtonStyle.primary,
            emoji="💎"
        )
        continue_button.callback = self.continue_to_prices
        self.add_item(continue_button)
    
    def _create_toggle_callback(self, member_id):
        """Create a callback function for donation toggle buttons."""
        async def callback(interaction):
            # Toggle donation status
            if member_id in self.donations:
                del self.donations[member_id]
                style = discord.ButtonStyle.secondary
                label_prefix = "💰"
            else:
                self.donations[member_id] = True
                style = discord.ButtonStyle.success
                label_prefix = "✅"
            
            # Update button style
            for item in self.children:
                if hasattr(item, 'custom_id') and item.custom_id == f"donate_{member_id}":
                    item.style = style
                    username = self.participants_data[member_id]['username'][:18]
                    item.label = f"{label_prefix} {username}"
                    break
            
            await interaction.response.edit_message(view=self)
        
        return callback
    
    async def participants_selected(self, interaction: discord.Interaction):
        """Handle participant selection for donations."""
        try:
            # Update donations based on selection
            self.donations = {}
            for value in self.participant_select.values:
                member_id = int(value)
                self.donations[member_id] = True
            
            donation_count = len(self.donations)
            total_participants = len(self.participants_data)
            
            embed = discord.Embed(
                title="💰 Donation Selection Updated",
                description=f"**{donation_count}** of **{total_participants}** participants selected for donation",
                color=discord.Color.green() if donation_count > 0 else discord.Color.blue()
            )
            
            if donation_count > 0:
                donor_names = [self.participants_data[mid]['username'] for mid in self.donations.keys()]
                embed.add_field(
                    name="Donating Participants",
                    value="\n".join([f"• {name}" for name in donor_names[:10]]),
                    inline=False
                )
                if len(donor_names) > 10:
                    embed.add_field(name="And more...", value=f"+ {len(donor_names) - 10} others", inline=False)
            
            embed.add_field(
                name="Next Step",
                value="Click **Continue to Price Setup** to proceed with UEX ore price configuration",
                inline=False
            )
            
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error updating donations: {str(e)}",
                ephemeral=True
            )
    
    async def continue_to_prices(self, interaction: discord.Interaction):
        """Continue to UEX price setup."""
        try:
            # Create price setup view
            price_view = UEXPriceSetupView(self.participants_data, self.event_id, self.ore_prices, self.donations)
            
            embed = discord.Embed(
                title="💎 UEX Ore Price Setup",
                description="Review and edit ore prices, then enter SCU amounts for calculation",
                color=discord.Color.blue()
            )
            
            # Show current price summary
            price_summary = []
            for ore_name, price_data in self.ore_prices.items():
                if isinstance(price_data, dict) and 'max_price' in price_data:
                    price = price_data['max_price']
                    display_name = price_data.get('display_name', ore_name)
                    price_summary.append(f"**{display_name}**: {price:,.0f} aUEC/SCU")
                else:
                    price_summary.append(f"**{ore_name}**: {price_data:,.0f} aUEC/SCU")
            
            if price_summary:
                embed.add_field(
                    name="Current UEX Prices",
                    value="\n".join(price_summary),
                    inline=False
                )
            
            donation_count = len(self.donations)
            embed.add_field(
                name="Donation Status",
                value=f"💰 {donation_count} participants donating their earnings",
                inline=True
            )
            
            await interaction.response.edit_message(embed=embed, view=price_view)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error setting up prices: {str(e)}",
                ephemeral=True
            )


class UEXPriceSetupView(discord.ui.View):
    """View for editing UEX ore prices and entering SCU amounts."""
    
    def __init__(self, participants_data, event_id, ore_prices, donations):
        super().__init__(timeout=300)  # 5 minute timeout
        self.participants_data = participants_data
        self.event_id = event_id
        self.ore_prices = ore_prices.copy()  # Make editable copy
        self.donations = donations
        
        # Add edit price buttons for each ore type
        for ore_name, price_data in list(self.ore_prices.items())[:4]:  # Limit to 4 main ores
            display_name = price_data.get('display_name', ore_name) if isinstance(price_data, dict) else ore_name
            button = discord.ui.Button(
                label=f"Edit {display_name[:15]}",
                style=discord.ButtonStyle.secondary,
                emoji="💎"
            )
            button.callback = self._create_price_edit_callback(ore_name)
            self.add_item(button)
        
        # SCU amounts and calculation button
        scu_button = discord.ui.Button(
            label="Enter SCU Amounts & Calculate",
            style=discord.ButtonStyle.primary,
            emoji="⚖️",
            row=2
        )
        scu_button.callback = self.enter_scu_amounts
        self.add_item(scu_button)
    
    def _create_price_edit_callback(self, ore_name):
        """Create callback for price editing."""
        async def callback(interaction):
            price_data = self.ore_prices[ore_name]
            current_price = price_data.get('max_price', price_data) if isinstance(price_data, dict) else price_data
            display_name = price_data.get('display_name', ore_name) if isinstance(price_data, dict) else ore_name
            
            modal = PriceEditModal(ore_name, display_name, current_price, self)
            await interaction.response.send_modal(modal)
        
        return callback
    
    async def enter_scu_amounts(self, interaction: discord.Interaction):
        """Show modal for SCU amounts and final calculation."""
        try:
            modal = EnhancedPayrollCalculationModal(
                self.participants_data, 
                self.event_id, 
                self.ore_prices, 
                self.donations
            )
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error opening SCU calculation: {str(e)}",
                ephemeral=True
            )


class PriceEditModal(discord.ui.Modal, title='Edit Ore Price'):
    """Modal for editing individual ore prices."""
    
    def __init__(self, ore_name, display_name, current_price, parent_view):
        super().__init__(timeout=300)
        self.ore_name = ore_name
        self.parent_view = parent_view
        
        self.price_input = discord.ui.TextInput(
            label=f'{display_name} Price (aUEC per SCU)',
            placeholder=f'Current: {current_price:,.0f} aUEC/SCU',
            default=str(int(current_price)),
            max_length=10,
            required=True
        )
        self.add_item(self.price_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Update the ore price."""
        try:
            new_price = float(self.price_input.value.replace(',', ''))
            
            # Update price in parent view
            if isinstance(self.parent_view.ore_prices[self.ore_name], dict):
                self.parent_view.ore_prices[self.ore_name]['max_price'] = new_price
            else:
                self.parent_view.ore_prices[self.ore_name] = new_price
            
            # Update embed to show new prices
            embed = discord.Embed(
                title="💎 UEX Ore Price Setup - Updated",
                description="Ore price updated successfully. Review prices and continue to SCU calculation.",
                color=discord.Color.green()
            )
            
            # Show updated price summary
            price_summary = []
            for ore_name, price_data in self.parent_view.ore_prices.items():
                if isinstance(price_data, dict) and 'max_price' in price_data:
                    price = price_data['max_price']
                    display_name = price_data.get('display_name', ore_name)
                    prefix = "🆕 " if ore_name == self.ore_name else ""
                    price_summary.append(f"{prefix}**{display_name}**: {price:,.0f} aUEC/SCU")
                else:
                    prefix = "🆕 " if ore_name == self.ore_name else ""
                    price_summary.append(f"{prefix}**{ore_name}**: {price_data:,.0f} aUEC/SCU")
            
            embed.add_field(
                name="Updated UEX Prices",
                value="\n".join(price_summary),
                inline=False
            )
            
            donation_count = len(self.parent_view.donations)
            embed.add_field(
                name="Donation Status",
                value=f"💰 {donation_count} participants donating their earnings",
                inline=True
            )
            
            await interaction.response.edit_message(embed=embed, view=self.parent_view)
            
        except ValueError:
            await interaction.response.send_message(
                f"❌ Invalid price format: {self.price_input.value}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error updating price: {str(e)}",
                ephemeral=True
            )


class EventSelectionView(discord.ui.View):
    """View for selecting which mining event to process payroll for."""
    
    def __init__(self, events_data):
        super().__init__(timeout=180)  # 3 minute timeout
        self.events_data = events_data
        
        # Create select menu with available events
        options = []
        for event_id, event_name, start_time, channel_name in events_data:
            # Format the display text
            time_str = start_time.strftime("%Y-%m-%d %H:%M")
            label = f"{event_name} - {time_str}"
            description = f"Channel: {channel_name}"
            
            options.append(discord.SelectOption(
                label=label[:100],  # Discord limit
                description=description[:100],  # Discord limit
                value=str(event_id)
            ))
        
        if options:
            self.event_select = discord.ui.Select(
                placeholder="Select a mining event for payroll...",
                options=options[:25]  # Discord limit
            )
            self.event_select.callback = self.event_selected
            self.add_item(self.event_select)
    
    async def event_selected(self, interaction: discord.Interaction):
        """Handle event selection - now starts enhanced workflow."""
        try:
            selected_event_id = int(self.event_select.values[0])
            
            # Get participants for the event
            participants_data = await self._get_event_participants(selected_event_id)
            if not participants_data:
                await interaction.response.send_message(
                    "❌ No participants found for this mining event",
                    ephemeral=True
                )
                return
            
            # Get ore prices
            ore_prices = await self._fetch_uex_prices()
            
            # Show participant donation selection view
            donation_view = ParticipantDonationView(participants_data, selected_event_id, ore_prices)
            
            embed = discord.Embed(
                title="👥 Select Participants for Donation",
                description=f"Found **{len(participants_data)}** participants in this mining event.\n\n"
                           "Select participants who want to **donate their earnings** to others.\n"
                           "Donated amounts will be redistributed among non-donating participants.",
                color=discord.Color.blue()
            )
            
            # Show participant preview
            participant_preview = []
            for member_id, data in list(participants_data.items())[:10]:
                hours = data['hours']
                participant_preview.append(f"• **{data['username']}** - {hours:.1f} hours")
            
            embed.add_field(
                name=f"Participants ({len(participants_data)} total)",
                value="\n".join(participant_preview) + (f"\n+ {len(participants_data) - 10} more..." if len(participants_data) > 10 else ""),
                inline=False
            )
            
            embed.add_field(
                name="How Donations Work",
                value="• Selected participants donate their calculated earnings\n"
                      "• Donations are redistributed to remaining participants\n" 
                      "• Final payouts reflect both original earnings + donation bonuses",
                inline=False
            )
            
            await interaction.response.edit_message(embed=embed, view=donation_view)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error selecting event: {str(e)}",
                ephemeral=True
            )
    
    async def _get_event_participants(self, event_id):
        """Get participants for a specific event."""
        try:
            from database.operations import get_mining_session_participants
            from config.settings import get_database_url
            
            db_url = get_database_url()
            if not db_url:
                return None
            
            participants_data = get_mining_session_participants(db_url, event_id=event_id)
            if not participants_data:
                return None
            
            participants = {}
            for member_id, username, total_time_seconds, primary_channel_id, last_activity, is_org_member in participants_data:
                if total_time_seconds > 30:  # Minimum 30 seconds participation
                    participants[int(member_id)] = {
                        'username': username,
                        'duration': total_time_seconds,
                        'is_org_member': is_org_member,
                        'hours': total_time_seconds / 3600,
                        'primary_channel': primary_channel_id,
                        'last_activity': last_activity
                    }
            
            return participants
            
        except Exception as e:
            print(f"Error getting event participants: {e}")
            return None
    
    async def _fetch_uex_prices(self):
        """Fetch current UEX ore prices using cached data."""
        try:
            from services.uex_cache import get_uex_cache
            
            cache = get_uex_cache()
            cached_prices = await cache.get_ore_prices(category="ores")
            
            if not cached_prices:
                print("❌ No UEX price data available from cache")
                return {}
            
            # Convert cache format to expected format
            ore_prices = {}
            for code, data in cached_prices.items():
                ore_name = data.get('name', code).upper()
                
                print(f"🔍 Processing cache item: {code} -> {ore_name} (price: {data.get('price_sell', 0)})")
                
                # Try multiple matching strategies for ORE_TYPES
                matched_key = None
                
                # Strategy 1: Direct name match
                if ore_name in ORE_TYPES:
                    matched_key = ore_name
                
                # Strategy 2: Code match
                if not matched_key and code.upper() in ORE_TYPES:
                    matched_key = code.upper()
                
                # Strategy 3: Partial name matching (remove " (ORE)" suffix etc)
                if not matched_key:
                    clean_name = ore_name.replace(' (ORE)', '').replace(' (RAW)', '').strip()
                    if clean_name in ORE_TYPES:
                        matched_key = clean_name
                
                # Strategy 4: Look for any ORE_TYPES key contained in the name
                if not matched_key:
                    for ore_key in ORE_TYPES.keys():
                        if ore_key in ore_name or ore_name in ore_key:
                            matched_key = ore_key
                            break
                
                if matched_key and data.get('price_sell', 0) > 0:
                    ore_prices[matched_key] = {
                        'max_price': float(data['price_sell']),
                        'display_name': ORE_TYPES[matched_key],
                        'code': data.get('code', code),
                        'kind': 'commodity'
                    }
                    print(f"✅ Matched {ore_name} -> {matched_key}: {data['price_sell']}")
                else:
                    print(f"❌ No match for {ore_name} (code: {code})")
            
            print(f"✅ Retrieved {len(ore_prices)} ore prices from cache")
            return ore_prices
                        
        except Exception as e:
            print(f"❌ Error fetching cached UEX prices: {e}")
            import traceback
            traceback.print_exc()
            return {}


class EnhancedPayrollCalculationModal(discord.ui.Modal, title='Sunday Mining - Final Payroll Calculation'):
    """Enhanced modal with donation support and custom UEX prices."""
    
    def __init__(self, participants_data, event_id, ore_prices, donations):
        super().__init__(timeout=300)  # 5 minute timeout
        self.participants_data = participants_data
        self.event_id = event_id
        self.ore_prices = ore_prices
        self.donations = donations
        
        # Show donation summary in modal description
        donation_count = len(donations)
        total_participants = len(participants_data)
        
        # Total value field - pre-filled with calculation but editable
        self.total_value = discord.ui.TextInput(
            label='Total Mining Value (aUEC) - Editable',
            placeholder='Auto-calculated from custom UEX prices + SCU amounts, or enter manually',
            max_length=15,
            required=True
        )
        
        # Ore amounts field for SCU tracking
        self.ore_amounts = discord.ui.TextInput(
            label='Ore Amounts (SCU)',
            placeholder='e.g., Quantanium: 50, Laranite: 100, Beryl: 75',
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=True
        )
        
        # Donation summary field (read-only)
        donation_summary = f"{donation_count} participants donating earnings to {total_participants - donation_count} recipients"
        self.donation_info = discord.ui.TextInput(
            label=f'Donation Summary ({donation_count} donors)',
            placeholder='Donation earnings will be redistributed automatically',
            default=donation_summary,
            max_length=100,
            required=False
        )
        
        self.add_item(self.total_value)
        self.add_item(self.ore_amounts) 
        self.add_item(self.donation_info)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Calculate and display enhanced payroll distribution with donations."""
        try:
            # Calculate total value from ore amounts using custom UEX prices
            total_value = 0
            
            if self.ore_amounts.value:
                calculated_value = await self._calculate_total_value_from_ores(self.ore_amounts.value)
                if calculated_value and calculated_value > 0:
                    if not self.total_value.value or self.total_value.value.lower() == "calculate":
                        total_value = calculated_value
                    else:
                        try:
                            total_value = float(self.total_value.value.replace(',', ''))
                        except ValueError:
                            total_value = calculated_value
            
            if total_value <= 0:
                try:
                    total_value = float(self.total_value.value.replace(',', ''))
                    if total_value <= 0:
                        await interaction.response.send_message(
                            "❌ Total value must be greater than 0",
                            ephemeral=True
                        )
                        return
                except ValueError:
                    await interaction.response.send_message(
                        f"❌ Invalid total value format: {self.total_value.value}",
                        ephemeral=True
                    )
                    return
            
            # Calculate enhanced participation shares with donations
            distribution_data = await self._calculate_enhanced_participation_shares(total_value)
            
            if not distribution_data:
                await interaction.response.send_message(
                    "❌ No valid participants for payroll distribution",
                    ephemeral=True
                )
                return
            
            # Create enhanced payroll embed
            embed = await self._create_enhanced_payroll_embed(
                distribution_data, 
                total_value,
                self.ore_amounts.value
            )
            
            # Finalize event
            await self._finalize_event(total_value, self.ore_amounts.value, interaction)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error calculating enhanced payroll: {str(e)}",
                ephemeral=True
            )
            import traceback
            traceback.print_exc()
    
    async def _calculate_total_value_from_ores(self, ore_text):
        """Calculate total value from ore amounts using custom UEX prices."""
        try:
            if not self.ore_prices:
                return None
            
            total_value = 0
            ore_breakdown = []
            
            # Parse ore amounts from text
            ore_entries = ore_text.split(',')
            
            for entry in ore_entries:
                if ':' not in entry:
                    continue
                
                ore_name, amount_str = entry.split(':', 1)
                ore_name = ore_name.strip().upper()
                
                try:
                    amount = float(amount_str.strip())
                    
                    # Find matching ore in our custom prices
                    price_per_scu = None
                    for price_ore_name, price_data in self.ore_prices.items():
                        if ore_name in price_ore_name.upper():
                            price_per_scu = price_data.get('max_price', price_data) if isinstance(price_data, dict) else price_data
                            break
                    
                    if price_per_scu and amount > 0:
                        ore_value = amount * price_per_scu
                        total_value += ore_value
                        ore_breakdown.append(f"{ore_name}: {amount} SCU × {price_per_scu:,.0f} = {ore_value:,.0f} aUEC")
                    
                except ValueError:
                    continue
            
            print(f"✅ Enhanced ore calculation: {total_value:,.0f} aUEC total")
            for line in ore_breakdown:
                print(f"   {line}")
            
            return total_value
            
        except Exception as e:
            print(f"Error calculating ore values with custom prices: {e}")
            return None
    
    async def _calculate_enhanced_participation_shares(self, total_value):
        """Calculate enhanced payroll with donation redistribution."""
        try:
            if not self.participants_data:
                return None
            
            # Calculate base time shares
            total_time = sum(data['duration'] for data in self.participants_data.values())
            if total_time == 0:
                return None
            
            # Step 1: Calculate base payouts for everyone
            base_payouts = {}
            donated_amount = 0
            recipient_ids = []
            
            for member_id, data in self.participants_data.items():
                time_share = data['duration'] / total_time
                base_payout = total_value * time_share
                
                if member_id in self.donations:
                    # This participant is donating their earnings
                    donated_amount += base_payout
                    base_payouts[member_id] = {
                        'base_payout': base_payout,
                        'final_payout': 0,  # Donating everything
                        'donation_bonus': 0,
                        'is_donor': True,
                        **data
                    }
                else:
                    # This participant will receive donations
                    recipient_ids.append(member_id)
                    base_payouts[member_id] = {
                        'base_payout': base_payout,
                        'final_payout': base_payout,  # Will be increased by donation bonus
                        'donation_bonus': 0,  # To be calculated
                        'is_donor': False,
                        **data
                    }
            
            # Step 2: Redistribute donated amount among recipients
            if donated_amount > 0 and recipient_ids:
                # Calculate recipient time share (only among non-donors)
                recipient_total_time = sum(self.participants_data[rid]['duration'] for rid in recipient_ids)
                
                for member_id in recipient_ids:
                    if recipient_total_time > 0:
                        recipient_time_share = self.participants_data[member_id]['duration'] / recipient_total_time
                        donation_bonus = donated_amount * recipient_time_share
                        
                        base_payouts[member_id]['donation_bonus'] = donation_bonus
                        base_payouts[member_id]['final_payout'] += donation_bonus
            
            print(f"✅ Enhanced payroll calculated: {donated_amount:,.0f} aUEC donated by {len(self.donations)} participants")
            
            return {
                'participants': base_payouts,
                'total_donated': donated_amount,
                'donor_count': len(self.donations),
                'recipient_count': len(recipient_ids),
                'total_value': total_value
            }
            
        except Exception as e:
            print(f"Error calculating enhanced participation shares: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _create_enhanced_payroll_embed(self, distribution_data, total_value, ore_amounts):
        """Create enhanced payroll embed showing donations."""
        try:
            participants = distribution_data['participants']
            total_donated = distribution_data['total_donated']
            donor_count = distribution_data['donor_count']
            recipient_count = distribution_data['recipient_count']
            
            embed = discord.Embed(
                title="💰 Enhanced Sunday Mining Payroll Distribution",
                description=f"**Total Mining Value:** {total_value:,.0f} aUEC\n"
                           f"**💸 Total Donated:** {total_donated:,.0f} aUEC by {donor_count} miners\n"
                           f"**🎁 Recipients:** {recipient_count} miners receiving donation bonuses",
                color=discord.Color.gold(),
                timestamp=datetime.now()
            )
            
            # Separate donors and recipients
            donors = {k: v for k, v in participants.items() if v['is_donor']}
            recipients = {k: v for k, v in participants.items() if not v['is_donor']}
            
            # Show recipients with bonuses
            if recipients:
                recipient_lines = []
                for member_id, data in sorted(recipients.items(), key=lambda x: x[1]['final_payout'], reverse=True)[:15]:
                    base = data['base_payout']
                    bonus = data['donation_bonus']
                    final = data['final_payout']
                    hours = data['hours']
                    
                    if bonus > 0:
                        recipient_lines.append(f"• **{data['username']}** - {final:,.0f} aUEC ({hours:.1f}h) *+{bonus:,.0f} bonus*")
                    else:
                        recipient_lines.append(f"• **{data['username']}** - {final:,.0f} aUEC ({hours:.1f}h)")
                
                embed.add_field(
                    name=f"🎁 Recipients ({len(recipients)} miners)",
                    value="\n".join(recipient_lines),
                    inline=False
                )
            
            # Show donors
            if donors:
                donor_lines = []
                for member_id, data in donors.items():
                    donated = data['base_payout']
                    hours = data['hours']
                    donor_lines.append(f"• **{data['username']}** - Donated {donated:,.0f} aUEC ({hours:.1f}h) 💝")
                
                embed.add_field(
                    name=f"💝 Generous Donors ({len(donors)} miners)",
                    value="\n".join(donor_lines),
                    inline=False
                )
            
            # Show ore breakdown if available
            if ore_amounts:
                embed.add_field(
                    name="⛏️ Ore Collection Summary",
                    value=f"```{ore_amounts}```",
                    inline=False
                )
            
            # Summary stats
            total_participants = len(participants)
            avg_payout = sum(p['final_payout'] for p in participants.values()) / len(recipients) if recipients else 0
            
            embed.add_field(name="📊 Summary", value=(
                f"**Total Participants:** {total_participants}\n"
                f"**Average Payout:** {avg_payout:,.0f} aUEC\n"
                f"**Donation Rate:** {(donor_count/total_participants*100):.1f}%"
            ), inline=True)
            
            embed.set_footer(text="Enhanced Payroll System • Donations redistributed based on participation time")
            
            return embed
            
        except Exception as e:
            print(f"Error creating enhanced payroll embed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _finalize_event(self, total_value, ore_amounts, interaction):
        """Finalize the mining event with enhanced data."""
        try:
            # Update event in database with final totals
            from config.settings import get_database_url
            from database.connection import get_legacy_connection
            
            db_url = get_database_url()
            if not db_url:
                return
            
            conn = get_legacy_connection(db_url)
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE mining_events 
                    SET total_value_auec = %s, 
                        status = 'completed',
                        payroll_processed = true,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE event_id = %s
                """, (total_value, self.event_id))
                
                conn.commit()
            conn.close()
            
            print(f"✅ Enhanced mining event {self.event_id} finalized with {total_value:,.0f} aUEC")
            
        except Exception as e:
            print(f"Error finalizing enhanced event: {e}")
            import traceback
            traceback.print_exc()


class PayrollCalculationModal(discord.ui.Modal, title='Sunday Mining - Payroll Calculation'):
    """Legacy modal for payroll officer to enter total mining haul and calculate shares."""
    
    def __init__(self, ore_prices=None, event_id=None):
        super().__init__(timeout=300)  # 5 minute timeout
        self.ore_prices = ore_prices or {}
        self.event_id = event_id
        
        # Pre-calculate price display from ore prices
        price_display = []
        
        for ore_name, ore_display in ORE_TYPES.items():
            price = self.ore_prices.get(ore_name, 0)
            if price > 0:
                price_display.append(f"{ore_display}: {price:,.0f} aUEC/SCU")
        
        # Total value field - pre-filled with calculation but editable
        self.total_value = discord.ui.TextInput(
            label='Total Mining Value (aUEC) - Editable',
            placeholder='Auto-calculated from UEX prices + SCU amounts, or enter manually',
            max_length=15,
            required=True
        )
        
        # Ore amounts field for SCU tracking
        self.ore_amounts = discord.ui.TextInput(
            label='Ore Amounts (SCU)',
            placeholder='e.g., Quantanium: 50, Laranite: 100, Beryl: 75',
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=True
        )
        
        self.add_item(self.total_value)
        self.add_item(self.ore_amounts)

    async def on_submit(self, interaction: discord.Interaction):
        """Calculate and display payroll distribution."""
        try:
            # First, try to auto-calculate from ore amounts
            total_value = 0
            
            if self.ore_amounts.value:
                # Calculate from SCU amounts using current UEX prices
                calculated_value = await self._calculate_total_value_from_ores(self.ore_amounts.value)
                if calculated_value and calculated_value > 0:
                    # If total_value field is empty or "calculate", use auto-calculated
                    if not self.total_value.value or self.total_value.value.lower() == "calculate":
                        total_value = calculated_value
                    else:
                        # User provided manual override
                        try:
                            total_value = float(self.total_value.value.replace(',', ''))
                        except ValueError:
                            total_value = calculated_value  # Fall back to calculated
            
            # If no valid total from calculation, parse manual entry
            if total_value <= 0:
                try:
                    total_value = float(self.total_value.value.replace(',', ''))
                    if total_value <= 0:
                        await interaction.response.send_message(
                            "❌ Total value must be greater than 0",
                            ephemeral=True
                        )
                        return
                except ValueError:
                    await interaction.response.send_message(
                        f"❌ Invalid total value format: {self.total_value.value}",
                        ephemeral=True
                    )
                    return
            
            # Calculate participation shares for this event
            participation_data = await self._calculate_participation_shares(total_value, self.event_id)
            
            if not participation_data:
                await interaction.response.send_message(
                    "❌ No participation data available. Make sure a mining session is active or was recently completed.",
                    ephemeral=True
                )
                return
            
            # Create payroll embed
            embed = await self._create_payroll_distribution_embed(
                participation_data, 
                total_value,
                self.ore_amounts.value
            )
            
            # Close the event in database and generate PDF
            await self._finalize_event(total_value, self.ore_amounts.value, interaction)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error calculating payroll: {str(e)}",
                ephemeral=True
            )
    
    async def _calculate_total_value_from_ores(self, ore_text):
        """Calculate total value from ore amounts using current UEX prices."""
        try:
            if not self.ore_prices:
                return None
            
            total_value = 0
            
            # Parse ore amounts from text like "Quantanium: 50, Laranite: 100"
            ore_entries = ore_text.split(',')
            
            for entry in ore_entries:
                if ':' not in entry:
                    continue
                
                ore_name, amount_str = entry.split(':', 1)
                ore_name = ore_name.strip().upper()
                
                try:
                    amount = float(amount_str.strip())
                    
                    # Find matching ore in our ORE_TYPES dict
                    matching_ore = None
                    for ore_key, ore_display in ORE_TYPES.items():
                        if ore_key == ore_name or ore_display.upper() == ore_name:
                            matching_ore = ore_key
                            break
                    
                    if matching_ore and matching_ore in self.ore_prices:
                        ore_value = amount * self.ore_prices[matching_ore]['max_price']
                        total_value += ore_value
                        print(f"Added {matching_ore}: {amount} SCU × {self.ore_prices[matching_ore]['max_price']} = {ore_value:,.0f} aUEC")
                    else:
                        print(f"Warning: No price data for {ore_name}")
                
                except ValueError:
                    print(f"Warning: Invalid amount for {ore_name}: {amount_str}")
                    continue
            
            return total_value if total_value > 0 else None
            
        except Exception as e:
            print(f"Error calculating total value from ores: {e}")
            return None
    
    async def _calculate_participation_shares(self, total_value, event_id=None):
        """Calculate how much each participant should receive based on time."""
        try:
            # Get participation data from enhanced mining tracking
            from database.operations import get_mining_session_participants
            from config.settings import get_database_url
            
            db_url = get_database_url()
            if not db_url:
                return None
            
            # Get mining participants - if event_id provided, get for that event, otherwise recent
            if event_id:
                participants_data = await self._get_event_participants(db_url, event_id)
            else:
                participants_data = get_mining_session_participants(db_url, hours_back=8)
            
            if not participants_data:
                return None
            
            participants = {}
            total_time = 0
            
            # Process participants with aggregated time across all channels
            for member_id, username, total_time_seconds, primary_channel_id, last_activity, is_org_member in participants_data:
                if total_time_seconds > 30:  # Minimum 30 seconds participation
                    participants[int(member_id)] = {
                        'username': username,
                        'duration': total_time_seconds,  # This is now aggregated across all channels
                        'is_org_member': is_org_member,
                        'hours': total_time_seconds / 3600,
                        'primary_channel': primary_channel_id,  # Channel where most time was spent
                        'last_activity': last_activity
                    }
                    total_time += total_time_seconds
            
            if total_time == 0:
                return None
            
            # Calculate individual payouts based on time share
            for member_id, data in participants.items():
                time_share = data['duration'] / total_time
                
                # Equal pay for all participants - no guest penalty
                effective_share = time_share
                payout = total_value * effective_share
                
                data['time_share'] = time_share
                data['effective_share'] = effective_share
                data['payout'] = payout
            
            return {
                'participants': participants,
                'total_time': total_time,
                'total_value': total_value,
                'participant_count': len(participants)
            }
            
        except Exception as e:
            print(f"Error calculating participation shares: {e}")
            return None
    
    async def _create_payroll_distribution_embed(self, data, total_value, total_scu, notes):
        """Create the payroll distribution embed."""
        embed = discord.Embed(
            title="💰 Sunday Mining Payroll Distribution",
            description=f"Event: `{current_session.get('event_id', 'Recent Session')}`",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        # Session summary
        total_hours = data['total_time'] / 3600
        embed.add_field(
            name="📊 Session Summary",
            value=f"• Total Value: **{total_value:,.0f} aUEC**\n"
                  f"• Participants: **{data['participant_count']}** miners\n"
                  f"• Total Time: **{total_hours:.1f}** hours\n"
                  + (f"• Total SCU: **{total_scu}**\n" if total_scu else ""),
            inline=False
        )
        
        # Top participants
        sorted_participants = sorted(
            data['participants'].items(),
            key=lambda x: x[1]['payout'],
            reverse=True
        )
        
        participant_list = []
        for member_id, pdata in sorted_participants[:10]:  # Top 10
            percentage = pdata['time_share'] * 100
            participant_list.append(
                f"• **{pdata['username']}**: {pdata['payout']:,.0f} aUEC "
                f"({pdata['hours']:.1f}h • {percentage:.1f}%)"
            )
        
        if participant_list:
            embed.add_field(
                name="👥 Payout Distribution",
                value="\n".join(participant_list),
                inline=False
            )
        
        # Additional participants if more than 10
        if len(sorted_participants) > 10:
            remaining = len(sorted_participants) - 10
            remaining_value = sum(p[1]['payout'] for p in sorted_participants[10:])
            embed.add_field(
                name=f"📋 Additional Participants (+{remaining})",
                value=f"Remaining {remaining} participants: {remaining_value:,.0f} aUEC total",
                inline=False
            )
        
        # Session notes
        if notes:
            embed.add_field(
                name="📝 Session Notes",
                value=notes,
                inline=False
            )
        
        # Calculation method
        embed.add_field(
            name="🧮 Calculation Method",
            value="• Payouts based on voice channel participation time\n"
                  "• Minimum 30 seconds participation required\n"
                  "• Time share = Individual time ÷ Total time\n"
                  "• Payout = Total value × Time share\n"
                  "• **Equal pay for all participants** (no guest penalties)",
            inline=False
        )
        
        embed.set_footer(text="Sunday Mining Payroll System • Time-based distribution")
        
        return embed
    
    async def _finalize_event(self, total_value, ore_amounts, interaction):
        """Close the event and generate PDF report."""
        try:
            from database.operations import close_mining_event, mark_pdf_generated
            from config.settings import get_database_url
            
            db_url = get_database_url()
            if not db_url or not self.event_id:
                print("⚠️ Cannot finalize event: missing database URL or event ID")
                return
            
            # Close the event in database
            close_mining_event(db_url, self.event_id, total_value)
            print(f"✅ Closed mining event {self.event_id} with total value {total_value:,.0f} aUEC")
            
            # Generate and send PDF report
            pdf_file = await self._generate_event_pdf_report(total_value, ore_amounts)
            
            if pdf_file:
                # Mark PDF as generated in database
                mark_pdf_generated(db_url, self.event_id)
                
                # Send PDF as follow-up message
                try:
                    await interaction.followup.send(
                        "📄 **Sunday Mining Report Generated**\n"
                        f"Event closed and PDF report created for Event #{self.event_id}",
                        file=pdf_file
                    )
                    print(f"✅ PDF report generated and sent for event {self.event_id}")
                except Exception as e:
                    print(f"❌ Error sending PDF: {e}")
                    await interaction.followup.send(
                        f"⚠️ Event closed successfully, but PDF could not be sent: {str(e)}",
                        ephemeral=True
                    )
            else:
                await interaction.followup.send(
                    f"⚠️ Event #{self.event_id} closed, but PDF generation failed",
                    ephemeral=True
                )
                
        except Exception as e:
            print(f"❌ Error finalizing event: {e}")
            # Don't show error to user as main payroll calculation succeeded
    
    async def _generate_event_pdf_report(self, total_value, ore_amounts):
        """Generate enhanced PDF report for this specific event."""
        try:
            import io
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from config.settings import get_database_url
            
            db_url = get_database_url()
            if not db_url or not self.event_id:
                return None
            
            # Get event-specific participation data
            from database.operations import get_mining_session_participants
            participants_data = get_mining_session_participants(db_url, hours_back=24)
            
            if not participants_data:
                return None
            
            # Create PDF in memory
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title = Paragraph(f"Sunday Mining Operations Report - Event #{self.event_id}", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 20))
            
            # Event Summary
            total_participants = len(participants_data)
            total_time = sum(record[2] for record in participants_data)
            total_hours = total_time / 3600
            
            summary_text = f"""
            <b>Event Summary:</b><br/>
            • Event ID: {self.event_id}<br/>
            • Total Participants: {total_participants}<br/>
            • Total Mining Time: {total_hours:.1f} hours<br/>
            • Total Value: {total_value:,.0f} aUEC<br/>
            • Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
            """
            
            summary = Paragraph(summary_text, styles['Normal'])
            story.append(summary)
            story.append(Spacer(1, 20))
            
            # Ore Collection Summary
            if ore_amounts:
                ore_text = f"""
                <b>Ore Collection Details:</b><br/>
                {ore_amounts.replace(',', '<br/>')}<br/>
                """
                ore_summary = Paragraph(ore_text, styles['Normal'])
                story.append(ore_summary)
                story.append(Spacer(1, 15))
            
            # Participation table
            table_data = [['Participant', 'Time (Hours)', 'Primary Channel', 'Org Member', 'Share %']]
            
            for member_id, username, total_time_seconds, primary_channel_id, last_activity, is_org_member in participants_data:
                hours = total_time_seconds / 3600
                org_status = "Yes" if is_org_member else "No"
                share_pct = (total_time_seconds / total_time) * 100 if total_time > 0 else 0
                
                table_data.append([
                    username[:20],  # Truncate long names
                    f"{hours:.1f}",
                    f"Channel {primary_channel_id}",
                    org_status,
                    f"{share_pct:.1f}%"
                ])
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            
            return discord.File(buffer, filename=f"sunday_mining_event_{self.event_id}_{datetime.now().strftime('%Y%m%d')}.pdf")
            
        except Exception as e:
            print(f"Error generating event PDF report: {e}")
            return None


class SundayMiningCommands(commands.Cog):
    """Sunday Mining command group."""
    
    def __init__(self, bot):
        self.bot = bot
        # Set bot instance for voice tracking
        from handlers.voice_tracking import set_bot_instance
        set_bot_instance(bot)
        print("✅ Mining commands initialized with bot instance")
    
    @app_commands.command(name="redsundayminingstart", description="Start Sunday mining session with voice tracking")
    async def sunday_mining_start(self, interaction: discord.Interaction):
        """Start Sunday mining session."""
        try:
            # Check if session is already active
            if current_session['active']:
                embed = discord.Embed(
                    title="⚠️ Mining Session Already Active",
                    description=f"Session started: <t:{int(current_session['start_time'].timestamp())}:R>",
                    color=0xffaa00
                )
                await interaction.response.send_message(embed=embed)
                return
            
            # Create database event for participation tracking
            import sys
            from pathlib import Path
            
            # Add src to path for imports
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            
            from config.settings import get_database_url
            from database import operations as database_operations
            
            db_url = get_database_url()
            event_id = None
            
            print(f"🔍 DEBUG: Database URL available: {db_url is not None}")
            
            if db_url:
                try:
                    # Use interaction.guild.id for proper guild-aware event creation
                    print(f"🔍 Creating mining event for guild {interaction.guild.id} ({interaction.guild.name})")
                    print(f"🔍 Database URL: {db_url[:50]}...")
                    print(f"🔍 Event date: {datetime.now().date()}")
                    print(f"🔍 Event name: Sunday Mining - {datetime.now().strftime('%Y-%m-%d')}")
                    
                    event_id = database_operations.create_mining_event(
                        db_url, 
                        interaction.guild.id, 
                        datetime.now().date(),
                        f"Sunday Mining - {datetime.now().strftime('%Y-%m-%d')}"
                    )
                    
                    print(f"🔍 create_mining_event returned: {event_id} (type: {type(event_id)})")
                    
                    if event_id is None:
                        print(f"❌ create_mining_event returned None - database operation failed")
                        print(f"❌ Check database logs for specific error details")
                    else:
                        print(f"✅ Created mining event {event_id} in guild {interaction.guild.name}")
                        print(f"🎯 Event ID {event_id} will be used for participation tracking")
                        
                except Exception as e:
                    print(f"❌ Exception during database event creation: {e}")
                    import traceback
                    print(f"Full traceback: {traceback.format_exc()}")
                    event_id = None
            else:
                print(f"❌ No database URL available, cannot create mining event")
                print(f"🔍 Database URL check result: {get_database_url()}")
            
            current_session.update({
                'active': True,
                'start_time': datetime.now(),
                'event_id': event_id,  # Store event_id for participation tracking
                'participants': {}
            })
            
            # Set bot instance for voice tracking before starting channels
            from handlers.voice_tracking import set_bot_instance
            set_bot_instance(self.bot)
            
            # Start voice tracking for all Sunday mining channels
            from handlers.voice_tracking import set_bot_instance
            
            # Ensure bot instance is set for voice operations
            set_bot_instance(interaction.client)
            
            mining_channels = get_sunday_mining_channels(interaction.guild.id)
            print(f"🔍 DEBUG: Retrieved mining channels: {mining_channels}")
            print(f"🔍 DEBUG: Mining channels type: {type(mining_channels)}")
            print(f"🔍 DEBUG: Mining channels keys: {list(mining_channels.keys()) if mining_channels else 'None'}")
            
            dispatch_join_success = False
            dispatch_error = None
            
            for channel_name, channel_id in mining_channels.items():
                # Only join the dispatch channel (check if channel name contains 'dispatch' - case insensitive)
                should_join = 'dispatch' in channel_name.lower() or 'main' in channel_name.lower()
                print(f"🔍 DEBUG: Channel '{channel_name}' -> lowercase: '{channel_name.lower()}' -> contains 'dispatch' or 'main': {should_join}")
                print(f"Adding channel {channel_name} ({channel_id}) to tracking, join={should_join}")
                
                try:
                    success = await add_tracked_channel(int(channel_id), should_join=should_join)
                    if should_join:  # This is the dispatch channel
                        dispatch_join_success = success
                        if not success:
                            dispatch_error = "Bot failed to join dispatch channel - check permissions"
                except Exception as e:
                    if should_join:  # This is the dispatch channel
                        dispatch_join_success = False
                        dispatch_error = f"Error joining dispatch: {str(e)}"
                    print(f"❌ Error adding channel {channel_name} ({channel_id}): {e}")
            
            # Log dispatch channel join result for debugging
            dispatch_channel_found = any('dispatch' in name.lower() or 'main' in name.lower() for name in mining_channels.keys())
            if dispatch_channel_found:
                if dispatch_join_success:
                    print("✅ Bot successfully joined dispatch channel")
                else:
                    print(f"❌ Bot failed to join dispatch channel: {dispatch_error}")
            else:
                print("⚠️ No dispatch/main channel configured in mining channels")
            
            start_voice_tracking()
            
            # Create success embed
            embed = discord.Embed(
                title="🚀 Sunday Mining Session Started",
                description="Voice tracking and participation logging is now active",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            session_details = f"• Started: <t:{int(datetime.now().timestamp())}:t>\n• Status: Active tracking"
            
            if event_id:
                session_details += f"\n• **Event ID**: `{event_id}` (for payroll reference)"
            else:
                session_details += f"\n• ⚠️ Database event creation failed - payroll may not work properly"
            
            embed.add_field(
                name="📊 Session Details",
                value=session_details,
                inline=False
            )
            
            # List tracked channels with current members
            mining_channels = get_sunday_mining_channels(interaction.guild.id)
            channel_list_items = []
            dispatch_join_status = None
            
            for name, channel_id in mining_channels.items():
                try:
                    # Get the actual channel object to display proper name and members
                    print(f"🔍 DEBUG: Looking up channel {name} with ID {channel_id}")
                    channel = interaction.guild.get_channel(int(channel_id))
                    print(f"🔍 DEBUG: Channel object found: {channel is not None}, type: {type(channel) if channel else 'None'}")
                    
                    if channel and hasattr(channel, 'members'):
                        # Count current members (excluding bots)
                        human_members = [member for member in channel.members if not member.bot]
                        member_count = len(human_members)
                        
                        if member_count == 0:
                            member_status = "Empty"
                        else:
                            # Show first 3 member names, then count if more
                            member_names = [member.display_name for member in human_members[:3]]
                            if member_count > 3:
                                member_status = f"{', '.join(member_names)} +{member_count-3} more"
                            else:
                                member_status = ', '.join(member_names)
                        
                        # Check if this is dispatch channel for bot join status
                        if 'dispatch' in name.lower():
                            bot_in_channel = any(member.id == interaction.client.user.id for member in channel.members)
                            dispatch_join_status = f"{'✅' if bot_in_channel else '❌'} Bot {'joined' if bot_in_channel else 'not in'} dispatch"
                        
                        channel_list_items.append(f"• **{name.title()}**: {channel.name} - *{member_status}*")
                    elif channel:
                        channel_list_items.append(f"• **{name.title()}**: {channel.name} - *Text Channel*")
                    else:
                        channel_list_items.append(f"• **{name.title()}**: Channel ID {channel_id} - *Not Found*")
                except (ValueError, TypeError) as e:
                    channel_list_items.append(f"• **{name.title()}**: Invalid ID {channel_id}")
                    print(f"⚠️ Error processing channel {name} ({channel_id}): {e}")
            
            channel_list = "\n".join(channel_list_items)
            
            # Add dispatch status if we found it
            dispatch_status_text = ""
            if dispatch_join_status:
                dispatch_status_text = f"\n\n{dispatch_join_status}"
            
            embed.add_field(
                name="🎤 Mining Channel Status",
                value=channel_list + dispatch_status_text,
                inline=False
            )
            
            # Add dispatch troubleshooting if there was an issue
            if dispatch_error:
                # Find the dispatch/main channel ID for troubleshooting
                dispatch_channel_id = "N/A"
                for name, channel_id in mining_channels.items():
                    if 'dispatch' in name.lower() or 'main' in name.lower():
                        dispatch_channel_id = channel_id
                        break
                
                embed.add_field(
                    name="⚠️ Dispatch Channel Issue",
                    value=f"{dispatch_error}\n\n**Troubleshooting:**\n• Check bot has 'Connect' permission in dispatch channel\n• Verify channel ID `{dispatch_channel_id}` is correct\n• Ensure bot can see the voice channel",
                    inline=False
                )
            
            embed.add_field(
                name="📝 Next Steps",
                value="1. **Look for the bot in Dispatch channel** - this confirms tracking is active\n2. Join any tracked voice channels to track participation\n3. Mine ore and deposit in central storage\n4. Use `/redsundayminingstop` when done\n5. Payroll officer uses `/redpayroll calculate` to calculate distribution",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error starting mining session: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="redsundayminingstop", description="Stop the current Sunday mining session")
    async def sunday_mining_stop(self, interaction: discord.Interaction):
        """Stop Sunday mining session."""
        try:
            if not current_session['active']:
                embed = discord.Embed(
                    title="⚠️ No Active Mining Session",
                    description="Use `/redsundayminingstart` to begin a session",
                    color=0xffaa00
                )
                await interaction.response.send_message(embed=embed)
                return
            
            # Calculate session duration
            duration = datetime.now() - current_session['start_time']
            duration_hours = duration.total_seconds() / 3600
            
            # Stop voice tracking
            mining_channels = get_sunday_mining_channels(interaction.guild.id)
            for channel_id in mining_channels.values():
                await remove_tracked_channel(int(channel_id))
            
            stop_voice_tracking()
            
            # Get participants data
            participants_text = "No participants tracked"
            participant_count = 0
            
            try:
                # Try to get participants from database first
                if current_session.get('event_id'):
                    from database.operations import get_mining_session_participants
                    from config.settings import get_database_url
                    
                    db_url = get_database_url()
                    if db_url:
                        participants_data = get_mining_session_participants(db_url, event_id=current_session['event_id'])
                        if participants_data:
                            participant_count = len(participants_data)
                            # Group participants by name and sum their time
                            participant_summary = {}
                            for p in participants_data:
                                name = p[2]  # participant_name is 3rd element
                                duration_mins = p[7] / 60 if len(p) > 7 else 0  # duration_seconds converted to minutes
                                if name in participant_summary:
                                    participant_summary[name] += duration_mins
                                else:
                                    participant_summary[name] = duration_mins
                            
                            # Create display text
                            if participant_summary:
                                participants_list = []
                                for name, total_mins in sorted(participant_summary.items()):
                                    participants_list.append(f"• {name}: {total_mins:.1f} mins")
                                participants_text = "\n".join(participants_list[:15])  # Limit to 15 to avoid embed limits
                                if len(participant_summary) > 15:
                                    participants_text += f"\n• ... and {len(participant_summary) - 15} more"
                
                # Fallback to in-memory tracking
                if participant_count == 0:
                    from handlers.voice_tracking import get_all_mining_participants
                    in_memory_participants = get_all_mining_participants(interaction.client)
                    if in_memory_participants:
                        participant_count = len(in_memory_participants)
                        participants_list = []
                        for member_id, data in in_memory_participants.items():
                            username = data.get('username', f'User {member_id}')
                            total_mins = data.get('total_time', 0) / 60
                            participants_list.append(f"• {username}: {total_mins:.1f} mins")
                        participants_text = "\n".join(participants_list[:15])
                        if len(in_memory_participants) > 15:
                            participants_text += f"\n• ... and {len(in_memory_participants) - 15} more"
                            
            except Exception as e:
                print(f"❌ Error retrieving participants: {e}")
                participants_text = "Error retrieving participant data"
            
            # Create session summary
            embed = discord.Embed(
                title="⏹️ Sunday Mining Session Ended", 
                description=f"Event ID: {current_session.get('event_id', 'None')}",
                color=0xff6b6b,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📊 Session Summary",
                value=f"• Duration: {duration_hours:.1f} hours\n• Participants: {participant_count}\n• 🤖 Bot has left all voice channels",
                inline=False
            )
            
            if participant_count > 0:
                embed.add_field(
                    name="👥 Participants",
                    value=participants_text,
                    inline=False
                )
            
            # Calculate total ore collected - removed since payroll officer handles this
            embed.add_field(
                name="💰 Next Steps",
                value="Payroll officer should use `/redpayroll calculate` to determine earnings distribution",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Reset session
            current_session.update({
                'active': False,
                'start_time': None,
                'event_id': None
            })
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error stopping mining session: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="redpayroll", description="Calculate Sunday mining payroll distribution (Admin/OrgLeaders only)")
    @app_commands.describe(
        action="Choose to calculate payroll or view summary (PDF auto-generated with calculation)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Calculate Payroll", value="calculate"),
        app_commands.Choice(name="View Participation Summary", value="summary"),
        app_commands.Choice(name="Show Current Ore Prices", value="prices")
    ])
    async def payroll(self, interaction: discord.Interaction, action: str):
        """Handle payroll calculation for authorized officers."""
        try:
            # Check if user has required permissions
            if not can_manage_payroll(interaction.user):
                await interaction.response.send_message(
                    "❌ Access denied. Only Admin or OrgLeaders can manage payroll.",
                    ephemeral=True
                )
                return
            
            if action == "calculate":
                await interaction.response.defer()
                
                # Get open mining events
                from config.settings import get_database_url
                db_url = get_database_url()
                
                if not db_url:
                    await interaction.followup.send(
                        "❌ Database connection not available",
                        ephemeral=True
                    )
                    return
                
                # Get recent Sunday mining events
                events = await self._get_mining_events(db_url, interaction.guild.id)
                
                if not events:
                    # No events found - provide helpful message
                    embed = discord.Embed(
                        title="❌ No Mining Events Found",
                        description="No recent Sunday mining events found. Start a mining session first with `/redsundayminingstart`",
                        color=0xff0000
                    )
                    embed.add_field(
                        name="Troubleshooting", 
                        value="• Make sure you've started a mining session\n• Check if events are being created in the database\n• Verify guild ID matches", 
                        inline=False
                    )
                    await interaction.followup.send(embed=embed)
                    return
                
                # Show event selection view with enhanced info
                view = EventSelectionView(events)
                embed = discord.Embed(
                    title="📋 Select Mining Event for Payroll",
                    description="Choose which Sunday mining event to process payroll for:",
                    color=0x3498db
                )
                # Add event info to embed
                if events:
                    event_list = ""
                    for i, event in enumerate(events[:5], 1):  # Show first 5 events
                        # Unpack based on get_open_mining_events format: id, guild_id, event_date, start_time, name, status, ...
                        event_id, guild_id, event_date, event_time, event_name, *rest = event
                        event_list += f"{i}. **{event_name}** - {event_time}\n"
                    embed.add_field(name="Available Events", value=event_list, inline=False)
                
                await interaction.followup.send(embed=embed, view=view)
            
            elif action == "summary":
                await interaction.response.defer()
                
                # Show current participation summary without calculating payroll
                summary_embed = await self._create_participation_summary()
                
                if summary_embed:
                    await interaction.followup.send(embed=summary_embed)
                else:
                    embed = discord.Embed(
                        title="⚠️ No Participation Data",
                        description="No recent participation data available",
                        color=0xffaa00
                    )
                    await interaction.followup.send(embed=embed)
            
            elif action == "prices":
                await interaction.response.defer()
                
                # Show current UEX ore prices
                ore_prices = await self._fetch_uex_prices()
                
                if ore_prices:
                    embed = await self._create_ore_prices_embed(ore_prices)
                    await interaction.followup.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="❌ UEX API Error",
                        description="Could not fetch current ore prices from UEX Corp",
                        color=0xff0000
                    )
                    await interaction.followup.send(embed=embed)
        
        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"❌ Error in payroll command: {str(e)}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"❌ Error in payroll command: {str(e)}"
                )
    
    async def _create_participation_summary(self) -> Optional[discord.Embed]:
        """Create a summary of current participation without calculating payroll."""
        try:
            from database.operations import get_mining_session_participants
            from config.settings import get_database_url
            
            db_url = get_database_url()
            if not db_url:
                return None
            
            # Get recent mining participants
            participants_data = get_mining_session_participants(db_url, hours_back=8)
            
            if not participants_data:
                return None
            
            embed = discord.Embed(
                title="📊 Current Mining Participation Summary",
                description=f"Event: `{current_session.get('event_id', 'Recent Activity')}`",
                color=0x3498db,
                timestamp=datetime.now()
            )
            
            total_time = sum(record[2] for record in participants_data)
            total_hours = total_time / 3600
            
            embed.add_field(
                name="🎯 Session Overview",
                value=f"• Participants: **{len(participants_data)}**\n"
                      f"• Total Time: **{total_hours:.1f}** hours\n"
                      f"• Average Time: **{(total_time/len(participants_data))/60:.1f}** minutes",
                inline=False
            )
            
            # Top participants with channel switching info
            participant_list = []
            for i, (member_id, username, total_time_seconds, primary_channel_id, last_activity, is_org_member) in enumerate(participants_data[:10]):
                hours = total_time_seconds / 3600
                minutes = (total_time_seconds % 3600) / 60
                org_badge = "🏢" if is_org_member else "👤"
                
                # Get primary channel name
                try:
                    primary_channel = self.bot.get_channel(int(primary_channel_id))
                    channel_name = primary_channel.name if primary_channel else "Unknown"
                except (ValueError, TypeError, AttributeError):
                    channel_name = "Unknown"
                
                if hours >= 1:
                    time_str = f"{hours:.1f}h"
                else:
                    time_str = f"{minutes:.0f}m"
                
                participant_list.append(f"{org_badge} **{username}**: {time_str} (Primary: {channel_name})")
            
            embed.add_field(
                name="👥 Participation Rankings",
                value="\n".join(participant_list),
                inline=False
            )
            
            embed.add_field(
                name="💡 Channel Switching",
                value="• Participants are tracked across all mining channels\n"
                      "• Primary channel = channel with most time spent\n" 
                      "• Total time = cumulative across all channels",
                inline=False
            )
            
            embed.add_field(
                name="💡 Next Steps",
                value="Use `/redpayroll calculate` to enter total mining value and calculate distribution",
                inline=False
            )
            
            embed.set_footer(text="Enhanced Mining System • Multi-Channel Tracking")
            
            return embed
            
        except Exception as e:
            print(f"Error creating participation summary: {e}")
            return None
    
    async def _auto_end_session(self, duration_hours: float):
        """Automatically end session after specified duration."""
        await asyncio.sleep(duration_hours * 3600)  # Convert hours to seconds
        
        if current_session['active']:
            # Stop tracking and leave voice channels
            mining_channels = get_sunday_mining_channels(None)  # Use None since we don't have guild context here
            for channel_id in mining_channels.values():
                await remove_tracked_channel(int(channel_id))
            stop_voice_tracking()
            
            # Reset session
            current_session['active'] = False
            print(f"✅ Auto-ended Sunday mining session: {current_session.get('event_id', 'Unknown')}")
    
    async def _fetch_uex_prices(self) -> Optional[Dict]:
        """Fetch current ore prices from UEX API - uses highest sell price per SCU."""
        try:
            headers = {
                'Authorization': f'Bearer {UEX_API_CONFIG["bearer_token"]}',
                'Accept': 'application/json'
            }
            
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    UEX_API_CONFIG['base_url'], 
                    headers=headers,
                    timeout=UEX_API_CONFIG.get('timeout', 30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        ore_prices = {}
                        
                        # Track highest prices per ore (multiple entries per ore across locations)
                        for commodity in data.get('data', []):
                            commodity_name = commodity.get('name', '').upper()
                            
                            # Only process mineral ores we care about
                            if (commodity.get('is_mineral') == 1 and 
                                commodity.get('is_extractable') == 1 and
                                commodity_name in ORE_TYPES):
                                
                                # Use sell price (what miners get when selling)
                                price = float(commodity.get('price_sell', 0))
                                
                                if price > 0:
                                    # Keep highest price for each ore across all locations
                                    if commodity_name not in ore_prices or price > ore_prices[commodity_name]['max_price']:
                                        ore_prices[commodity_name] = {
                                            'max_price': price,
                                            'min_price': float(commodity.get('price_buy', 0)),
                                            'avg_price': price,  # For display purposes
                                            'display_name': ORE_TYPES[commodity_name],
                                            'code': commodity.get('code', ''),
                                            'kind': commodity.get('kind', '')
                                        }
                        
                        print(f"✅ Fetched {len(ore_prices)} ore prices from UEX API")
                        return ore_prices
                    else:
                        print(f"❌ UEX API error: HTTP {response.status}")
                        return None
        
        except Exception as e:
            print(f"❌ Error fetching UEX prices: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _fetch_detailed_uex_prices(self, category: str = "ores"):
        """Fetch detailed UEX prices using cached data."""
        try:
            from services.uex_cache import get_uex_cache
            
            cache = get_uex_cache()
            cached_prices = await cache.get_ore_prices(category=category)
            
            if not cached_prices:
                print(f"❌ No UEX {category} price data available from cache")
                return None
            
            # Convert cache format to expected detailed format
            commodities = {}
            for code, data in cached_prices.items():
                commodity_name = data.get('name', code).upper()
                
                commodities[commodity_name] = {
                    'name': data.get('name', 'Unknown'),
                    'code': data.get('code', code),
                    'kind': 'commodity',
                    'price_sell': float(data.get('price_sell', 0)),
                    'price_buy': float(data.get('price_buy', 0)),
                    'is_mineral': True,  # Assume true for cached ore data
                    'is_extractable': True,  # Assume true for cached ore data
                    'is_illegal': False,  # Assume false for ores
                    'weight_scu': 1,  # Default weight
                    'commodity_id': code,
                    'locations': data.get('locations', []),
                    'location': 'Best Available Price',
                    'updated': data.get('updated', 'Unknown')
                }
            
            print(f"✅ Retrieved {len(commodities)} {category} from cache")
            return commodities
        
        except Exception as e:
            print(f"❌ Error fetching detailed cached UEX prices: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _create_detailed_price_embed(self, price_data: Dict, category: str) -> discord.Embed:
        """Create detailed price embed with location information."""
        category_names = {
            "ores": "Mineable Ores",
            "high_value": "High Value Commodities", 
            "all": "All Commodities"
        }
        
        embed = discord.Embed(
            title=f"📊 UEX Corp Price Check - {category_names.get(category, category.title())}",
            description="Live prices from UEX API with best selling locations",
            color=0x3498db,
            timestamp=datetime.now()
        )
        
        if not price_data:
            embed.add_field(
                name="❌ No Price Data",
                value="Could not fetch current commodity prices",
                inline=False
            )
            return embed
        
        # Sort by price (highest first)
        sorted_items = sorted(
            price_data.items(),
            key=lambda x: x[1]['price_sell'],
            reverse=True
        )
        
        # Split into chunks for better readability - use single wide columns
        chunk_size = 8
        chunks = [sorted_items[i:i + chunk_size] for i in range(0, min(len(sorted_items), 25), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            price_list = []
            for commodity_key, commodity_data in chunk:
                # Add indicators for special commodities
                indicators = []
                if commodity_data.get('is_illegal'):
                    indicators.append("⚠️")
                if commodity_data.get('is_mineral'):
                    indicators.append("⛏️")
                
                indicator_str = "".join(indicators) + " " if indicators else ""
                
                # Get location information for best price
                location_info = "Location Unknown"
                locations = commodity_data.get('locations', [])
                if locations:
                    # Find location with highest sell price
                    best_location = max(locations, 
                                      key=lambda x: x.get('sell_price', 0))
                    location_name = best_location.get('name', 'Unknown Location')
                    # Truncate long location names for better readability
                    if len(location_name) > 30:
                        location_name = location_name[:27] + "..."
                    location_info = location_name
                
                # More spaced out formatting with better alignment
                price_list.append(
                    f"{indicator_str}**{commodity_data['name']}** ({commodity_data['code']})\n"
                    f"💰 **{commodity_data['price_sell']:,.0f}** aUEC/SCU\n"
                    f"📍 {location_info}"
                )
            
            field_name = f"💰 Prices & Locations ({i+1}/{len(chunks)})" if len(chunks) > 1 else "💰 Prices & Best Locations"
            embed.add_field(
                name=field_name,
                value="\n\n".join(price_list),  # Double spacing between items
                inline=False  # Always use full width for better readability
            )
        
        # Add summary statistics
        if price_data:
            prices = [p['price_sell'] for p in price_data.values()]
            embed.add_field(
                name="📈 Price Statistics",
                value=f"• Highest: **{max(prices):,.0f}** aUEC/SCU\n"
                      f"• Lowest: **{min(prices):,.0f}** aUEC/SCU\n" 
                      f"• Average: **{sum(prices)/len(prices):,.0f}** aUEC/SCU\n"
                      f"• Total Items: **{len(price_data)}**",
                inline=False
            )
        
        # Add legend
        embed.add_field(
            name="🔍 Legend",
            value="⛏️ Mineable Ore • ⚠️ Illegal Commodity • 📍 Best Selling Location\n"
                  "💡 Use `/redpayroll calculate` to calculate mining payouts",
            inline=False
        )
        
        embed.set_footer(text=f"Data from UEX Corp API • Category: {category_names.get(category, category)}")
        
        return embed
    
    async def _create_ore_prices_embed(self, ore_prices: Dict) -> discord.Embed:
        """Create an embed showing current ore prices with locations."""
        embed = discord.Embed(
            title="💰 Current Ore Prices & Best Locations",
            description="Live prices from UEX Corp API with highest price locations",
            color=0x3498db,
            timestamp=datetime.now()
        )
        
        if not ore_prices:
            embed.add_field(
                name="❌ No Price Data",
                value="Could not fetch current ore prices",
                inline=False
            )
            return embed
        
        # Get detailed price data with locations from cache
        try:
            from services.uex_cache import get_uex_cache
            cache = get_uex_cache()
            detailed_prices = await cache.get_ore_prices(category="ores")
        except Exception as e:
            print(f"⚠️ Could not get detailed location data: {e}")
            detailed_prices = {}
        
        # Sort ores by max price (highest first)
        sorted_ores = sorted(
            ore_prices.items(),
            key=lambda x: x[1]['max_price'],
            reverse=True
        )
        
        # Split into chunks for better readability (smaller chunks to accommodate location data)
        chunk_size = 6
        chunks = [sorted_ores[i:i + chunk_size] for i in range(0, len(sorted_ores), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            price_list = []
            for ore_key, price_data in chunk:
                price = price_data['max_price']
                ore_name = price_data['display_name']
                
                # Try to find location information using improved matching
                location_info = "Location Unknown"
                if detailed_prices:
                    # Debug: print available keys for first ore to understand the data structure
                    if i == 0 and ore_key == list(ore_prices.keys())[0]:
                        print(f"🔍 Debug ore prices structure - Looking for: {ore_key} ({ore_name})")
                        print(f"🔍 Available detailed cache keys: {list(detailed_prices.keys())[:5]}...")
                        if detailed_prices:
                            sample_key = list(detailed_prices.keys())[0]
                            print(f"🔍 Sample cache data structure: {detailed_prices[sample_key]}")
                    
                    # Look for this ore in detailed cache data with more flexible matching
                    found_data = None
                    
                    # Try exact code match first (most reliable)
                    if ore_key in detailed_prices:
                        found_data = detailed_prices[ore_key]
                    else:
                        # Try case-insensitive matching on codes and names
                        for code, cache_data in detailed_prices.items():
                            cache_name = cache_data.get('name', '').upper()
                            ore_key_upper = ore_key.upper()
                            ore_name_upper = ore_name.upper()
                            
                            if (code.upper() == ore_key_upper or 
                                cache_name == ore_key_upper or
                                cache_name == ore_name_upper or
                                ore_key_upper in cache_name or
                                cache_name in ore_key_upper):
                                found_data = cache_data
                                break
                    
                    if found_data:
                        # Find best location from locations array
                        locations = found_data.get('locations', [])
                        
                        if locations:
                            # Find location with highest sell price
                            best_location = max(locations, 
                                              key=lambda x: x.get('sell_price', 0))
                            location_name = best_location.get('name', 'Best Available Price')
                            
                            # Since UEX API v2.0 doesn't provide specific location data,
                            # just show a consistent message for all ores
                            location_info = "UEX Highest Price"
                        else:
                            location_info = "UEX Highest Price"
                    else:
                        location_info = "UEX Highest Price"
                
                price_list.append(
                    f"• **{ore_name}**: {price:,.0f} aUEC/SCU\n"
                    f"  📍 {location_info}"
                )
            
            field_name = f"💰 Ore Prices & Locations ({i+1}/{len(chunks)})" if len(chunks) > 1 else "💰 Ore Prices & Locations"
            embed.add_field(
                name=field_name,
                value="\n\n".join(price_list),
                inline=True if len(chunks) > 1 else False
            )
        
        embed.add_field(
            name="💡 Usage Tips",
            value="• Prices show the highest available sell price per location\n"
                  "• Use `/redpayroll calculate` to enter ore amounts and auto-calculate total value\n"
                  "• Prices update automatically every 24 hours from UEX Corp",
            inline=False
        )
        
        embed.set_footer(text="Data from UEX Corp • Cached with location data • Prices in aUEC per SCU")
        
        return embed
    
    async def _get_mining_events(self, db_url, guild_id):
        """Get open Sunday mining events for a specific guild."""
        try:
            from database.operations import get_open_mining_events
            
            print(f"🔍 Looking for mining events in guild {guild_id}")
            
            # Get open mining events for this guild
            events = get_open_mining_events(db_url, guild_id)
            print(f"📋 Found {len(events)} open mining events")
            
            if not events:
                # If no open events, get recent events from events table
                from database.operations import get_mining_events
                print(f"🔄 No open events found, searching recent events...")
                recent_events = get_mining_events(db_url, guild_id)
                
                if recent_events:
                    # Convert to same format as get_open_mining_events for consistency
                    events = []
                    for event in recent_events:
                        # Map from get_mining_events format to expected format
                        events.append((
                            event['id'], 
                            event['guild_id'], 
                            event['event_date'],
                            event['start_time'], 
                            event['event_name'],
                            event['status'],
                            event.get('total_participants', 0),
                            event.get('total_value', 0.0),
                            event.get('payroll_processed', False),
                            event.get('pdf_generated', False),
                            event.get('created_at'),
                            event.get('updated_at')
                        ))
                    print(f"📋 Found {len(events)} recent mining events as fallback")
                else:
                    events = []
            
            return events
            
        except Exception as e:
            print(f"❌ Error getting mining events: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return []
    
    async def _get_event_participants(self, db_url, event_id):
        """Get participants for a specific event."""
        try:
            from database.operations import get_mining_session_participants
            
            print(f"🔍 Getting participants for event {event_id}")
            # Use the unified function with event_id parameter
            participants = get_mining_session_participants(db_url, event_id=event_id)
            print(f"👥 Found {len(participants)} participants for event {event_id}")
            return participants
            
        except Exception as e:
            print(f"❌ Error getting event participants: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return []
    
    async def _generate_pdf_report(self):
        """Generate PDF report for Sunday mining session."""
        try:
            import io
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            
            # Get recent participation data
            from database.operations import get_mining_session_participants
            from config.settings import get_database_url
            
            db_url = get_database_url()
            if not db_url:
                return None
            
            participants_data = get_mining_session_participants(db_url, hours_back=24)
            
            if not participants_data:
                return None
            
            # Create PDF in memory
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title = Paragraph("Sunday Mining Operations Report", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 20))
            
            # Summary info
            total_participants = len(participants_data)
            total_time = sum(record[2] for record in participants_data)
            total_hours = total_time / 3600
            
            summary_text = f"""
            <b>Session Summary:</b><br/>
            • Total Participants: {total_participants}<br/>
            • Total Mining Time: {total_hours:.1f} hours<br/>
            • Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
            """
            
            summary = Paragraph(summary_text, styles['Normal'])
            story.append(summary)
            story.append(Spacer(1, 20))
            
            # Participation table
            table_data = [['Participant', 'Time (Hours)', 'Primary Channel', 'Org Member']]
            
            for member_id, username, total_time_seconds, primary_channel_id, last_activity, is_org_member in participants_data:
                hours = total_time_seconds / 3600
                org_status = "Yes" if is_org_member else "No"
                primary_channel = f"Channel {primary_channel_id}"
                
                table_data.append([
                    username[:20],  # Truncate long names
                    f"{hours:.1f}",
                    primary_channel,
                    org_status
                ])
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            
            return discord.File(buffer, filename=f"sunday_mining_report_{datetime.now().strftime('%Y%m%d')}.pdf")
            
        except Exception as e:
            print(f"Error generating PDF report: {e}")
            return None
    
    @app_commands.command(name="redpricecheck", description="Check live ore prices and locations from UEX API")
    @app_commands.describe(category="Category of commodities to check")
    @app_commands.choices(category=[
        app_commands.Choice(name="Ores (Mineable)", value="ores"),
        app_commands.Choice(name="All Commodities", value="all"),
        app_commands.Choice(name="High Value Only", value="high_value")
    ])
    async def price_check(self, interaction: discord.Interaction, category: str = "ores"):
        """Check current commodity prices from UEX API with location data."""
        try:
            await interaction.response.defer()
            
            # Fetch UEX data with location information
            price_data = await self._fetch_detailed_uex_prices(category)
            
            if not price_data:
                embed = discord.Embed(
                    title="❌ UEX API Error",
                    description="Could not fetch current price data from UEX Corp",
                    color=0xff0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Create price embed with location data
            embed = await self._create_detailed_price_embed(price_data, category)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error checking prices: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="redpricerefresh", description="Force refresh UEX price data immediately (Admin/OrgLeaders only)")
    @app_commands.describe(category="Category of commodities to refresh")
    @app_commands.choices(category=[
        app_commands.Choice(name="Ores (Mineable)", value="ores"),
        app_commands.Choice(name="All Commodities", value="all"),
        app_commands.Choice(name="High Value Only", value="high_value")
    ])
    async def force_price_refresh(self, interaction: discord.Interaction, category: str = "ores"):
        """Force refresh UEX price data bypassing the 24-hour cache."""
        try:
            # Check permissions
            if not can_manage_payroll(interaction.user):
                await interaction.response.send_message(
                    "❌ Access denied. Only Admin or OrgLeaders can force price refresh.",
                    ephemeral=True
                )
                return
            
            await interaction.response.defer()
            
            # Get UEX cache instance and force refresh
            from services.uex_cache import get_uex_cache
            
            cache = get_uex_cache()
            
            # Show current cache status before refresh
            cache_stats = cache.get_cache_stats()
            cache_key = f"prices_{category}"
            
            if cache_key in cache_stats.get("entries", {}):
                old_age = cache_stats["entries"][cache_key]["age_seconds"]
                old_age_minutes = old_age / 60
                old_valid = cache_stats["entries"][cache_key]["valid"]
            else:
                old_age_minutes = 0
                old_valid = False
            
            embed = discord.Embed(
                title="🔄 Forcing UEX Price Refresh",
                description=f"Bypassing cache to fetch fresh {category} data from UEX Corp API",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📊 Cache Status (Before)",
                value=f"• Age: {old_age_minutes:.1f} minutes\n"
                      f"• Valid: {'✅' if old_valid else '❌'}\n"
                      f"• Normal refresh interval: 24 hours",
                inline=True
            )
            
            # Force refresh the data
            print(f"🔄 Force refreshing {category} prices via admin command")
            fresh_prices = await cache.get_ore_prices(category, force_refresh=True)
            
            if fresh_prices:
                # Show success stats
                new_cache_stats = cache.get_cache_stats()
                new_stats = new_cache_stats["entries"][cache_key]
                
                embed.add_field(
                    name="✅ Refresh Complete",
                    value=f"• Fresh data retrieved from UEX API\n"
                          f"• Items updated: {new_stats['item_count']}\n"
                          f"• Cache age: 0 minutes (just refreshed)\n"
                          f"• Next auto-refresh: 24 hours",
                    inline=True
                )
                
                # Show sample of updated prices
                sample_prices = []
                for ore_code, price_data in list(fresh_prices.items())[:3]:
                    if isinstance(price_data, dict):
                        name = price_data.get('name', ore_code)
                        price = price_data.get('price_sell', 0)
                        sample_prices.append(f"• **{name}**: {price:,.0f} aUEC/SCU")
                
                if sample_prices:
                    embed.add_field(
                        name="💰 Sample Updated Prices",
                        value="\n".join(sample_prices),
                        inline=False
                    )
                
                embed.color = discord.Color.green()
                
            else:
                embed.add_field(
                    name="❌ Refresh Failed",
                    value="Could not fetch fresh data from UEX API\n"
                          "Check server logs for detailed error information",
                    inline=False
                )
                embed.color = discord.Color.red()
            
            embed.set_footer(text="Use /redpricecheck to see all current prices")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error forcing price refresh: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="redsundayminingtest", description="Run diagnostics for Sunday Mining voice channel issues (Admin only)")
    @app_commands.describe(
        test_type="Type of diagnostic test to run"
    )
    @app_commands.choices(test_type=[
        app_commands.Choice(name="All Tests", value="all"),
        app_commands.Choice(name="Database Schema", value="database"),
        app_commands.Choice(name="Voice Channels", value="voice"),
        app_commands.Choice(name="Bot Permissions", value="permissions"),
        app_commands.Choice(name="Voice Connection", value="connection"),
        app_commands.Choice(name="Guild Configuration", value="guild")
    ])
    async def sunday_mining_test(self, interaction: discord.Interaction, test_type: str = "all"):
        """Run comprehensive diagnostics for Sunday Mining system."""
        try:
            # Check admin permissions
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "❌ Access denied. Only administrators can run mining diagnostics.",
                    ephemeral=True
                )
                return
            
            await interaction.response.defer()
            
            # Import the testing framework
            from commands.mining.testing import SundayMiningTester
            
            # Create tester instance
            tester = SundayMiningTester(self.bot, interaction.guild)
            
            # Run specified tests
            if test_type == "all":
                results = await tester.run_all_tests()
            elif test_type == "database":
                results = await tester.test_database_schema()
            elif test_type == "voice":
                results = await tester.test_voice_channels()
            elif test_type == "permissions":
                results = await tester.test_bot_permissions()
            elif test_type == "connection":
                results = await tester.test_voice_connection()
            elif test_type == "guild":
                results = await tester.test_guild_configuration()
            else:
                results = {"error": "Invalid test type"}
            
            # Create results embed
            embed = discord.Embed(
                title=f"🔧 Sunday Mining Diagnostics - {test_type.title()}",
                description=f"Diagnostic results for {interaction.guild.name}",
                color=0x3498db,
                timestamp=datetime.now()
            )
            
            # Add test results
            if "error" in results:
                embed.add_field(
                    name="❌ Error",
                    value=results["error"],
                    inline=False
                )
            else:
                # Add results for each test category
                for category, tests in results.items():
                    if isinstance(tests, dict):
                        test_status = []
                        for test_name, result in tests.items():
                            status = "✅" if result.get("passed", False) else "❌"
                            test_status.append(f"{status} {test_name}")
                        
                        embed.add_field(
                            name=f"📋 {category.replace('_', ' ').title()}",
                            value="\n".join(test_status[:10]),  # Limit to 10 per field
                            inline=True
                        )
            
            # Add recommendation section
            recommendations = []
            
            if test_type in ["all", "voice", "connection"]:
                recommendations.append("• Check if bot has permission to join voice channels")
                recommendations.append("• Verify voice channel IDs in mining configuration")
                recommendations.append("• Ensure bot can see and access all mining channels")
            
            if test_type in ["all", "database"]:
                recommendations.append("• Verify database connection and schema")
                recommendations.append("• Check if mining channels are properly configured")
            
            if recommendations:
                embed.add_field(
                    name="💡 Common Solutions",
                    value="\n".join(recommendations),
                    inline=False
                )
            
            # Add next steps
            embed.add_field(
                name="🎯 Next Steps",
                value="1. Review failed tests above\n"
                      "2. Check bot permissions in voice channels\n"
                      "3. Verify mining channel configuration\n"
                      "4. Test with `/redsundayminingstart` after fixes",
                inline=False
            )
            
            embed.set_footer(text="Sunday Mining Diagnostics • Use results to troubleshoot issues")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error running diagnostics: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="redeventdiagnostics", description="Debug event creation and retrieval (Admin only)")
    @app_commands.default_permissions(administrator=True)
    async def event_diagnostics(self, interaction: discord.Interaction):
        """Diagnose event creation and retrieval issues."""
        try:
            await interaction.response.defer()
            
            from config.settings import get_database_url
            from database.connection import resolve_database_url
            from database.operations import get_open_mining_events
            import psycopg2
            
            db_url = get_database_url()
            guild_id = interaction.guild.id
            
            embed = discord.Embed(
                title="🔍 Event Diagnostics",
                description=f"Checking event creation and retrieval for guild {guild_id}",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            if not db_url:
                embed.add_field(
                    name="❌ Database Connection",
                    value="No database URL available",
                    inline=False
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Test database connection
            try:
                resolved_url = resolve_database_url(db_url)
                conn = psycopg2.connect(resolved_url)
                cursor = conn.cursor()
                
                embed.add_field(
                    name="✅ Database Connection",
                    value="Successfully connected to database",
                    inline=False
                )
                
                # Check events table schema with detailed info
                cursor.execute("""
                    SELECT column_name, data_type, character_maximum_length, is_nullable,
                           column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'events' 
                    ORDER BY ordinal_position
                """)
                
                schema_info = cursor.fetchall()
                schema_text = []
                event_id_details = None
                
                for row in schema_info:
                    col_name, data_type, max_length, nullable, default = row
                    if col_name == 'event_id':
                        event_id_details = row
                    
                    length_info = f"({max_length})" if max_length else ""
                    nullable_info = "NULL" if nullable == 'YES' else "NOT NULL"
                    default_info = f" DEFAULT {default}" if default else ""
                    
                    schema_text.append(f"• {col_name}: {data_type}{length_info} {nullable_info}{default_info}")
                
                embed.add_field(
                    name="📋 Table Schema",
                    value=f"```\n{chr(10).join(schema_text[:15])}\n```",
                    inline=False
                )
                
                # Special attention to event_id column for prefix compatibility
                if event_id_details:
                    col_name, data_type, max_length, nullable, default = event_id_details
                    can_store_prefixed = data_type in ['character varying', 'varchar', 'text', 'character']
                    max_length_ok = max_length is None or max_length >= 20  # Need at least 20 chars for prefixed IDs
                    
                    prefix_compat = "✅ Compatible" if (can_store_prefixed and max_length_ok) else "❌ Needs Migration"
                    
                    embed.add_field(
                        name="🏷️ Event ID Prefix Compatibility",
                        value=f"**Current**: {data_type}" + (f"({max_length})" if max_length else "") + f"\n"
                              f"**Prefixed ID Support**: {prefix_compat}\n"
                              f"**Required**: VARCHAR(50) or TEXT for prefixed IDs like 'sm-a7k2m9'",
                        inline=False
                    )
                
                # Check recent events in this guild
                cursor.execute("""
                    SELECT id, guild_id, name, 
                           CASE WHEN is_open THEN 'open' ELSE 'closed' END as status, 
                           event_date, created_at 
                    FROM events 
                    WHERE guild_id = %s AND created_at >= NOW() - INTERVAL '7 days'
                    ORDER BY created_at DESC 
                    LIMIT 5
                """, (int(guild_id),))
                
                recent_events = cursor.fetchall()
                
                if recent_events:
                    events_text = []
                    for event in recent_events:
                        events_text.append(
                            f"• ID: `{event[0]}` | Status: `{event[3]}` | Date: {event[4]} | Name: {event[2]}"
                        )
                    embed.add_field(
                        name="📅 Recent Events (Last 7 Days)",
                        value="\n".join(events_text),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="📅 Recent Events (Last 7 Days)",
                        value="❌ No events found in the last 7 days",
                        inline=False
                    )
                
                # Test get_open_mining_events function
                try:
                    open_events = get_open_mining_events(db_url, guild_id)
                    embed.add_field(
                        name="🔍 get_open_mining_events()",
                        value=f"Found {len(open_events)} open events" + (f"\n• First event ID: `{open_events[0]['id']}`" if open_events else ""),
                        inline=False
                    )
                except Exception as e:
                    embed.add_field(
                        name="❌ get_open_mining_events() Error",
                        value=f"Function failed: {str(e)[:200]}",
                        inline=False
                    )
                
                # Search for specific session ID (if provided)
                search_session = "sunday_20250909_180124"
                cursor.execute("""
                    SELECT event_id, guild_id, name, 
                           status, event_date, created_at 
                    FROM mining_events 
                    WHERE name ILIKE %s
                       OR event_id::text = %s
                    ORDER BY created_at DESC
                """, (f'%{search_session}%', search_session))
                
                session_results = cursor.fetchall()
                if session_results:
                    session_text = []
                    for event in session_results:
                        session_text.append(
                            f"• ID: `{event[0]}` | Name: {event[2]} | Status: `{event[3]}`"
                        )
                    embed.add_field(
                        name=f"🔍 Session ID Search: {search_session}",
                        value="\n".join(session_text),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=f"🔍 Session ID Search: {search_session}",
                        value="❌ No events found matching this session ID",
                        inline=False
                    )
                
                # Test creating a test event
                from datetime import date
                test_event_name = f"DIAGNOSTIC TEST - {datetime.now().strftime('%H:%M:%S')}"
                
                try:
                    from database.operations import create_mining_event
                    test_event_id = create_mining_event(
                        db_url,
                        guild_id,
                        date.today(),
                        test_event_name
                    )
                    
                    if test_event_id:
                        embed.add_field(
                            name="✅ Event Creation Test",
                            value=f"Successfully created test event: `{test_event_id}`\nName: {test_event_name}",
                            inline=False
                        )
                    else:
                        embed.add_field(
                            name="❌ Event Creation Test",
                            value="create_mining_event() returned None",
                            inline=False
                        )
                except Exception as e:
                    embed.add_field(
                        name="❌ Event Creation Test",
                        value=f"Failed to create test event: {str(e)[:200]}",
                        inline=False
                    )
                
                conn.close()
                
            except Exception as e:
                embed.add_field(
                    name="❌ Database Error",
                    value=f"Connection failed: {str(e)[:300]}",
                    inline=False
                )
            
            embed.set_footer(text="Use this information to troubleshoot event creation issues")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error running event diagnostics: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="redapidebug", description="Debug UEX API response structure (Admin only)")
    @app_commands.describe(
        commodity="Specific commodity code to debug (optional)",
        raw_output="Show raw JSON response"
    )
    @app_commands.default_permissions(administrator=True)
    async def debug_uex_api(self, interaction: discord.Interaction, commodity: str = None, raw_output: bool = False):
        """Debug the actual UEX API response to understand location data structure."""
        
        await interaction.response.defer()
        
        try:
            from services.uex_cache import get_uex_cache
            import json
            
            # Get fresh data from UEX API
            cache = get_uex_cache()
            
            # Force a fresh API call
            print("🔍 Making direct UEX API debug call...")
            raw_data = await cache._fetch_uex_api("ores")
            
            if not raw_data:
                await interaction.followup.send("❌ Failed to fetch UEX API data", ephemeral=True)
                return
            
            if raw_output:
                # Show raw JSON response (truncated for Discord limits)
                raw_json = json.dumps(raw_data, indent=2)
                if len(raw_json) > 1800:
                    raw_json = raw_json[:1800] + "...\n[TRUNCATED]"
                
                embed = discord.Embed(
                    title="🔍 Raw UEX API Response",
                    description=f"```json\n{raw_json}\n```",
                    color=0x00ff00
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Analyze structure
            if commodity:
                # Debug specific commodity
                commodity = commodity.upper()
                if commodity in raw_data:
                    item = raw_data[commodity]
                    
                    embed = discord.Embed(
                        title=f"🔍 UEX API Debug: {commodity}",
                        description=f"**{item.get('name', 'Unknown')}**",
                        color=0x00ff00
                    )
                    
                    # Show all available fields
                    embed.add_field(
                        name="📊 Basic Data",
                        value=f"• Price Sell: {item.get('price_sell', 'N/A')}\n• Price Buy: {item.get('price_buy', 'N/A')}\n• Code: {item.get('code', 'N/A')}",
                        inline=False
                    )
                    
                    # Show all keys in the item
                    all_keys = list(item.keys())
                    embed.add_field(
                        name="🗝️ All API Fields",
                        value=f"```{', '.join(all_keys)}```",
                        inline=False
                    )
                    
                    # Check for location data in various forms
                    location_fields = []
                    for key in ['locations', 'terminals', 'trades', 'prices', 'best_location', 'location_data']:
                        if key in item:
                            location_fields.append(f"• **{key}**: {type(item[key]).__name__} - {item[key]}")
                    
                    if location_fields:
                        location_text = '\n'.join(location_fields)
                        if len(location_text) > 1000:
                            location_text = location_text[:1000] + "...\n[TRUNCATED]"
                        embed.add_field(
                            name="📍 Location Data Found",
                            value=location_text,
                            inline=False
                        )
                    else:
                        embed.add_field(
                            name="❌ Location Data",
                            value="No location fields found in this commodity",
                            inline=False
                        )
                    
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Commodity '{commodity}' not found in API response", ephemeral=True)
            else:
                # Show general API structure
                embed = discord.Embed(
                    title="🔍 UEX API Structure Analysis",
                    description=f"Found **{len(raw_data)}** commodities in response",
                    color=0x00ff00
                )
                
                # Sample a few commodities to understand structure
                sample_items = list(raw_data.items())[:3]
                
                for code, item in sample_items:
                    # Check what location-related fields exist
                    location_keys = []
                    for key in item.keys():
                        if any(loc_word in key.lower() for loc_word in ['location', 'terminal', 'trade', 'price', 'sell', 'buy']):
                            location_keys.append(key)
                    
                    embed.add_field(
                        name=f"📦 {code} ({item.get('name', 'Unknown')})",
                        value=f"**Location-related fields**: {', '.join(location_keys) if location_keys else 'None'}\n**All fields**: {len(item.keys())} total",
                        inline=False
                    )
                
                # Show common field analysis
                all_fields = set()
                location_fields = set()
                for item in raw_data.values():
                    all_fields.update(item.keys())
                    for key in item.keys():
                        if any(loc_word in key.lower() for loc_word in ['location', 'terminal', 'trade', 'sell', 'buy']):
                            location_fields.add(key)
                
                embed.add_field(
                    name="🌐 All Fields Across API",
                    value=f"```{', '.join(sorted(all_fields))}```",
                    inline=False
                )
                
                embed.add_field(
                    name="📍 Potential Location Fields",
                    value=f"```{', '.join(sorted(location_fields)) if location_fields else 'None found'}```",
                    inline=False
                )
                
                embed.set_footer(text="Use 'commodity' parameter to debug a specific ore (e.g. QUANTAINIUM)")
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            await interaction.followup.send(f"❌ Debug error: {str(e)}", ephemeral=True)
            print(f"❌ UEX API debug error: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")

    @app_commands.command(name="redchanneldiag", description="Diagnose voice channel configuration (Admin only)")
    @app_commands.default_permissions(administrator=True)
    async def channel_diagnostic(self, interaction: discord.Interaction):
        """Diagnose voice channel configuration and permissions."""
        
        await interaction.response.defer(ephemeral=True)
        
        embed = discord.Embed(
            title="🔧 Voice Channel Diagnostics",
            description="Analyzing voice channel configuration and bot permissions",
            color=0x3498db,
            timestamp=datetime.now()
        )
        
        # Get configured mining channels
        from config.channels import get_sunday_mining_channels
        mining_channels = get_sunday_mining_channels(interaction.guild.id)
        
        embed.add_field(
            name="📋 Configured Mining Channels",
            value=f"Found {len(mining_channels)} configured channels:\n```" + 
                  "\n".join([f"{name}: {channel_id}" for name, channel_id in mining_channels.items()]) + "```",
            inline=False
        )
        
        # Check each channel
        channel_status = []
        actual_voice_channels = []
        
        for name, channel_id in mining_channels.items():
            try:
                channel = interaction.guild.get_channel(int(channel_id))
                if channel:
                    if hasattr(channel, 'members'):  # Voice channel
                        perms = channel.permissions_for(interaction.guild.me)
                        status = f"✅ **{name}**: `{channel.name}` (ID: {channel_id})"
                        status += f"\n   • Connect: {'✅' if perms.connect else '❌'}"
                        status += f"\n   • Speak: {'✅' if perms.speak else '❌'}"
                        status += f"\n   • View: {'✅' if perms.view_channel else '❌'}"
                        status += f"\n   • Members: {len([m for m in channel.members if not m.bot])}"
                        channel_status.append(status)
                    else:
                        channel_status.append(f"⚠️ **{name}**: `{channel.name}` - NOT a voice channel (ID: {channel_id})")
                else:
                    channel_status.append(f"❌ **{name}**: Channel not found (ID: {channel_id})")
            except Exception as e:
                channel_status.append(f"❌ **{name}**: Error - {str(e)} (ID: {channel_id})")
        
        if channel_status:
            embed.add_field(
                name="🎤 Channel Status & Permissions",
                value="\n".join(channel_status[:10]),  # Limit for Discord embed
                inline=False
            )
        
        # Show actual voice channels in guild
        voice_channels = [ch for ch in interaction.guild.channels if hasattr(ch, 'members')]
        if voice_channels:
            voice_list = []
            for ch in voice_channels[:15]:  # Limit display
                members = len([m for m in ch.members if not m.bot])
                voice_list.append(f"• `{ch.name}` (ID: {ch.id}) - {members} members")
            
            embed.add_field(
                name="🔍 All Voice Channels in Guild",
                value="\n".join(voice_list),
                inline=False
            )
        
        # Bot permissions check
        bot_perms = interaction.guild.me.guild_permissions
        embed.add_field(
            name="🤖 Bot Guild Permissions",
            value=f"• Connect: {'✅' if bot_perms.connect else '❌'}\n"
                  f"• Speak: {'✅' if bot_perms.speak else '❌'}\n"
                  f"• Move Members: {'✅' if bot_perms.move_members else '❌'}\n"
                  f"• Manage Channels: {'✅' if bot_perms.manage_channels else '❌'}",
            inline=False
        )
        
        embed.set_footer(text="Use this information to fix channel configuration issues")
        await interaction.followup.send(embed=embed)


async def setup(bot):
    """Setup function for the mining cog."""
    # Set bot instance for voice tracking
    from handlers.voice_tracking import set_bot_instance
    set_bot_instance(bot)
    
    cog = SundayMiningCommands(bot)
    await bot.add_cog(cog)
    
    # Debug: List the commands in this cog
    print(f"✅ Mining cog loaded with {len(cog.get_app_commands())} app commands:")
    for cmd in cog.get_app_commands():
        print(f"  • {cmd.name} - {cmd.description}")


# Legacy function for command registration compatibility
def register_commands(bot):
    """Register mining commands - now redirects to slash commands."""
    
    @bot.command(name="log_mining_results")
    async def log_mining_results_cmd(ctx):
        """Legacy function - redirects to new Sunday mining system."""
        embed = discord.Embed(
            title="🔄 Command Updated",
            description="This command has been replaced with the new Sunday Mining system!",
            color=0x3498db
        )
        embed.add_field(
            name="New Commands",
            value="• `/redsundayminingstart` - Start mining session\n• `/redpayroll` - Submit ore collections\n• `/redsundayminingstop` - End session",
            inline=False
        )
        await ctx.send(embed=embed)
    
    print("✅ Mining commands registered (legacy compatibility)")
