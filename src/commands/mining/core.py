"""
Sunday Mining Module for Red Legion Discord Bot

This module handles Sunday mining operations including:
- Voice participation tracking across 7 mining channels
- Ore collection reporting through Discord modals
- Automated payroll calculation using UEX API
- Mining session management and reporting

Commands:
- /sunday_mining_start: Start a Sunday mining session
- /sunday_mining_stop: Stop the current mining session 
- /payroll: Calculate and display payroll for the last session
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
    'session_id': None,
    'participants': {}  # {user_id: participation_data}
}


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
        """Handle event selection."""
        try:
            selected_event_id = int(self.event_select.values[0])
            
            # Get ore prices for the modal
            ore_prices = await self._fetch_uex_prices()
            
            # Show payroll calculation modal for selected event
            modal = PayrollCalculationModal(ore_prices, selected_event_id)
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error selecting event: {str(e)}",
                ephemeral=True
            )
    
    async def _fetch_uex_prices(self):
        """Fetch current UEX ore prices."""
        try:
            headers = {'Authorization': f'Bearer {UEX_API_CONFIG["bearer_token"]}'}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    UEX_API_CONFIG['base_url'], 
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        ore_prices = {}
                        
                        for commodity in data.get('data', []):
                            commodity_name = commodity.get('name', '').upper()
                            if commodity_name in ORE_TYPES:
                                ore_prices[commodity_name] = commodity.get('price_sell', 0)
                        
                        return ore_prices
                    
        except Exception as e:
            print(f"Error fetching UEX prices: {e}")
        
        return {}


class PayrollCalculationModal(discord.ui.Modal, title='Sunday Mining - Payroll Calculation'):
    """Modal for payroll officer to enter total mining haul and calculate shares."""
    
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
                
                # Apply org member bonus (org members get 100%, guests get 80%)
                if data['is_org_member']:
                    effective_share = time_share
                else:
                    effective_share = time_share * 0.8  # 20% reduction for non-org members
                
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
            description=f"Session: `{current_session.get('session_id', 'Unknown')}`",
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
                  "• Payout = Total value × Time share",
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
    
    @app_commands.command(name="red-sunday-mining-start", description="Start Sunday mining session with voice tracking")
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
            
            # Initialize session and create database event
            session_id = f"sunday_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create event in database
            import sys
            import importlib.util
            from pathlib import Path
            
            # Import from the specific operations.py file, not the operations/ directory
            operations_path = Path(__file__).parent.parent.parent / 'database' / 'operations.py'
            spec = importlib.util.spec_from_file_location("database_operations", operations_path)
            database_operations = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(database_operations)
            
            from config.settings import get_database_url
            db_url = get_database_url()
            event_id = None
            
            print(f"🔍 DEBUG: Database URL available: {db_url is not None}")
            
            if db_url:
                try:
                    # Use interaction.guild.id for proper guild-aware event creation
                    print(f"🔍 Creating mining event for guild {interaction.guild.id} ({interaction.guild.name})")
                    event_id = database_operations.create_mining_event(
                        db_url, 
                        interaction.guild.id, 
                        datetime.now().date(),
                        f"Sunday Mining - {datetime.now().strftime('%Y-%m-%d')}"
                    )
                    print(f"✅ Created mining event {event_id} for session {session_id} in guild {interaction.guild.name}")
                    
                    if event_id is None:
                        print(f"❌ create_mining_event returned None - database operation failed")
                    else:
                        print(f"🎯 Event ID {event_id} will be used for participation tracking")
                        
                except Exception as e:
                    print(f"⚠️ Could not create database event: {e}")
                    import traceback
                    print(f"Full traceback: {traceback.format_exc()}")
            else:
                print(f"❌ No database URL available, cannot create mining event")
            
            current_session.update({
                'active': True,
                'start_time': datetime.now(),
                'session_id': session_id,
                'event_id': event_id,  # Store event_id for later use
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
            
            for channel_name, channel_id in mining_channels.items():
                # Only join the dispatch channel (check if 'dispatch' is in the channel name)
                should_join = 'dispatch' in channel_name.lower()
                print(f"🔍 DEBUG: Channel '{channel_name}' -> lowercase: '{channel_name.lower()}' -> contains 'dispatch': {should_join}")
                print(f"Adding channel {channel_name} ({channel_id}) to tracking, join={should_join}")
                await add_tracked_channel(int(channel_id), should_join=should_join)
            
            start_voice_tracking()
            
            # Create success embed
            embed = discord.Embed(
                title="🚀 Sunday Mining Session Started",
                description=f"Session ID: `{session_id}`",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📊 Session Details",
                value=f"• Started: <t:{int(datetime.now().timestamp())}:t>\n• Status: Active tracking",
                inline=False
            )
            
            # List tracked channels
            mining_channels = get_sunday_mining_channels(interaction.guild.id)
            channel_list_items = []
            for name, channel_id in mining_channels.items():
                try:
                    # Get the actual channel object to display proper name
                    channel = interaction.guild.get_channel(int(channel_id))
                    if channel:
                        channel_list_items.append(f"• {name.title()}: {channel.name}")
                    else:
                        channel_list_items.append(f"• {name.title()}: Channel ID {channel_id}")
                except (ValueError, TypeError):
                    channel_list_items.append(f"• {name.title()}: Invalid ID {channel_id}")
            
            channel_list = "\n".join(channel_list_items)
            embed.add_field(
                name="🎤 Tracked Voice Channels",
                value=channel_list + "\n\n🤖 **Bot will join Dispatch channel** to indicate active tracking!",
                inline=False
            )
            
            embed.add_field(
                name="📝 Next Steps",
                value="1. **Look for the bot in Dispatch channel** - this confirms tracking is active\n2. Join any tracked voice channels to track participation\n3. Mine ore and deposit in central storage\n4. Use `/sunday_mining_stop` when done\n5. Payroll officer uses `/payroll` to calculate distribution",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error starting mining session: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="red-sunday-mining-stop", description="Stop the current Sunday mining session")
    async def sunday_mining_stop(self, interaction: discord.Interaction):
        """Stop Sunday mining session."""
        try:
            if not current_session['active']:
                embed = discord.Embed(
                    title="⚠️ No Active Mining Session",
                    description="Use `/sunday_mining_start` to begin a session",
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
            
            # Create session summary
            embed = discord.Embed(
                title="⏹️ Sunday Mining Session Ended",
                description=f"Session ID: `{current_session['session_id']}`",
                color=0xff6b6b,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📊 Session Summary",
                value=f"• Duration: {duration_hours:.1f} hours\n• Participants tracked via voice channels\n• 🤖 Bot has left all voice channels",
                inline=False
            )
            
            # Calculate total ore collected - removed since payroll officer handles this
            embed.add_field(
                name="💰 Next Steps",
                value="Payroll officer should use `/payroll calculate` to determine earnings distribution",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Reset session
            current_session.update({
                'active': False,
                'start_time': None,
                'session_id': None
            })
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error stopping mining session: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="red-payroll", description="Calculate Sunday mining payroll distribution (Admin/OrgLeaders only)")
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
                        description="No recent Sunday mining events found. Start a mining session first with `/sunday_mining_start`",
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
                        event_id, event_name, event_time, *rest = event
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
                description=f"Session: `{current_session.get('session_id', 'Recent Activity')}`",
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
                value="Use `/payroll calculate` to enter total mining value and calculate distribution",
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
            print(f"✅ Auto-ended Sunday mining session: {current_session['session_id']}")
    
    async def _fetch_uex_prices(self) -> Optional[Dict]:
        """Fetch current ore prices from UEX API."""
        try:
            headers = {
                'Authorization': f'Bearer {UEX_API_CONFIG["bearer_token"]}',
                'Accept': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(UEX_API_CONFIG['base_url'], headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Parse UEX data and map to our ore types
                        ore_prices = {}
                        for commodity in data.get('data', []):
                            commodity_name = commodity.get('name', '').upper()
                            if commodity_name in ORE_TYPES:
                                ore_prices[commodity_name] = {
                                    'max_price': float(commodity.get('price_max', 0)),
                                    'min_price': float(commodity.get('price_min', 0)),
                                    'avg_price': float(commodity.get('price_avg', 0)),
                                    'display_name': ORE_TYPES[commodity_name]
                                }
                        
                        return ore_prices
                    else:
                        print(f"UEX API error: {response.status}")
                        return None
        
        except Exception as e:
            print(f"Error fetching UEX prices: {e}")
            return None
    
    async def _create_ore_prices_embed(self, ore_prices: Dict) -> discord.Embed:
        """Create an embed showing current ore prices."""
        embed = discord.Embed(
            title="� Current Ore Prices",
            description="Live prices from UEX Corp API",
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
        
        # Sort ores by max price (highest first)
        sorted_ores = sorted(
            ore_prices.items(),
            key=lambda x: x[1]['max_price'],
            reverse=True
        )
        
        # Split into chunks for multiple fields
        chunk_size = 8
        chunks = [sorted_ores[i:i + chunk_size] for i in range(0, len(sorted_ores), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            price_list = []
            for ore_key, price_data in chunk:
                price_list.append(
                    f"• **{price_data['display_name']}**: {price_data['max_price']:,.0f} aUEC/SCU"
                )
            
            field_name = f"💰 Ore Prices ({i+1}/{len(chunks)})" if len(chunks) > 1 else "💰 Ore Prices"
            embed.add_field(
                name=field_name,
                value="\n".join(price_list),
                inline=True if len(chunks) > 1 else False
            )
        
        # Add calculation example
        if ore_prices:
            total_value = sum(p['max_price'] for p in ore_prices.values())
            embed.add_field(
                name="📊 Price Summary",
                value=f"• Highest: **{max(ore_prices.values(), key=lambda x: x['max_price'])['display_name']}** "
                      f"({max(p['max_price'] for p in ore_prices.values()):,.0f} aUEC/SCU)\n"
                      f"• Lowest: **{min(ore_prices.values(), key=lambda x: x['max_price'])['display_name']}** "
                      f"({min(p['max_price'] for p in ore_prices.values()):,.0f} aUEC/SCU)\n"
                      f"• Average: **{total_value/len(ore_prices):,.0f} aUEC/SCU**",
                inline=False
            )
        
        embed.add_field(
            name="💡 Usage Tips",
            value="• Use these prices to calculate total mining haul value\n"
                  "• Prices update in real-time from UEX Corp\n"
                  "• Use `/payroll calculate` and enter ore amounts to auto-calculate total value",
            inline=False
        )
        
        embed.set_footer(text="Data from UEX Corp • Prices in aUEC per SCU")
        
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
                # If no open events, get recent closed events as fallback for this guild
                import psycopg2
                conn = psycopg2.connect(db_url)
                c = conn.cursor()
                c.execute(
                    """
                    SELECT id, event_name, event_time, created_at
                    FROM events 
                    WHERE guild_id = %s 
                       AND (event_name ILIKE '%%sunday%%mining%%' OR event_name ILIKE '%%mining%%')
                       AND created_at >= NOW() - INTERVAL '7 days'
                    ORDER BY created_at DESC
                    LIMIT 10
                    """,
                    (guild_id,)
                )
                events = c.fetchall()
                conn.close()
                print(f"📋 Found {len(events)} recent events as fallback")
            
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
    
    @app_commands.command(name="red-sunday-mining-test", description="Run diagnostics for Sunday Mining voice channel issues (Admin only)")
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
                      "4. Test with `/sunday_mining_start` after fixes",
                inline=False
            )
            
            embed.set_footer(text="Sunday Mining Diagnostics • Use results to troubleshoot issues")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error running diagnostics: {str(e)}",
                ephemeral=True
            )


async def setup(bot):
    """Setup function for the mining cog."""
    # Set bot instance for voice tracking
    from handlers.voice_tracking import set_bot_instance
    set_bot_instance(bot)
    
    await bot.add_cog(SundayMiningCommands(bot))


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
            value="• `/sunday_mining_start` - Start mining session\n• `/payroll` - Submit ore collections\n• `/sunday_mining_stop` - End session",
            inline=False
        )
        await ctx.send(embed=embed)
    
    print("✅ Mining commands registered (legacy compatibility)")
