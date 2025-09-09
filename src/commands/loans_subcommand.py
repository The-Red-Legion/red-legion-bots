"""
Red Legion Loan Management System
Implements /red-loans subcommand group for organization loan management
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timezone, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class LoanConfirmationView(discord.ui.View):
    """Confirmation view for loan requests"""
    
    def __init__(self, loan_data: dict, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.loan_data = loan_data
        self.confirmed = False
    
    @discord.ui.button(label='Confirm Loan Request', style=discord.ButtonStyle.green, emoji='✅')
    async def confirm_loan(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirm and submit the loan request"""
        try:
            from ..database.database import Database
            
            db = Database()
            
            # Create the loan request
            loan_id = await db.create_loan_request(self.loan_data)
            
            embed = discord.Embed(
                title="✅ Loan Request Submitted",
                description="Your loan request has been submitted for review.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="Loan ID", value=f"`{loan_id}`", inline=True)
            embed.add_field(name="Amount", value=f"{self.loan_data['amount']:,} UEC", inline=True)
            embed.add_field(name="Status", value="Pending Approval", inline=True)
            
            embed.add_field(
                name="What's Next?",
                value="• Finance officers will review your request\n"
                      "• You'll be notified of the decision\n"
                      "• Use `/red-loans status` to check progress",
                inline=False
            )
            
            embed.set_footer(text="Red Legion Finance System")
            
            await interaction.response.edit_message(embed=embed, view=None)
            
            # Notify finance officers
            await self._notify_finance_officers(interaction, loan_id, self.loan_data)
            
        except Exception as e:
            logger.error(f"Error confirming loan: {e}")
            await interaction.response.send_message(
                "❌ Error submitting loan request. Please try again.",
                ephemeral=True
            )
    
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red, emoji='❌')
    async def cancel_loan(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel the loan request"""
        embed = discord.Embed(
            title="❌ Loan Request Cancelled",
            description="Your loan request has been cancelled.",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=None)
    
    async def _notify_finance_officers(self, interaction: discord.Interaction, loan_id: int, loan_data: dict):
        """Notify finance officers of new loan request"""
        try:
            from ..database.database import Database
            
            db = Database()
            settings = await db.get_loan_settings(str(interaction.guild_id))
            
            if not settings or not settings.get('finance_channel_id'):
                return
            
            channel = interaction.guild.get_channel(int(settings['finance_channel_id']))
            if not channel:
                return
            
            embed = discord.Embed(
                title="💰 New Loan Request",
                description=f"**{loan_data['borrower_name']}** has requested a loan",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="Loan ID", value=f"`{loan_id}`", inline=True)
            embed.add_field(name="Amount", value=f"{loan_data['amount']:,} UEC", inline=True)
            embed.add_field(name="Purpose", value=loan_data['purpose'], inline=True)
            
            if loan_data['repayment_plan']:
                embed.add_field(name="Repayment Plan", value=loan_data['repayment_plan'], inline=False)
            
            embed.add_field(
                name="Review Actions",
                value="Use `/red-loans approve` or `/red-loans deny` to process this request",
                inline=False
            )
            
            # Mention finance role if configured
            content = ""
            if settings.get('finance_officer_role_id'):
                content = f"<@&{settings['finance_officer_role_id']}>"
            
            await channel.send(content=content, embed=embed)
            
        except Exception as e:
            logger.error(f"Error notifying finance officers: {e}")

class RedLoansGroup(app_commands.Group):
    """Red Legion Loans command group"""
    
    def __init__(self):
        super().__init__(name='redloans', description='Organization loan management system')
    
    @app_commands.command(name='request', description='Request a loan from the organization')
    @app_commands.describe(
        amount='Loan amount in UEC',
        purpose='Purpose of the loan',
        repayment_plan='Your proposed repayment plan (optional)'
    )
    async def request_loan(self, interaction: discord.Interaction, amount: int, purpose: str, repayment_plan: str = None):
        """Request a loan from the organization"""
        try:
            from ..database.database import Database
            
            db = Database()
            
            # Validate amount
            if amount <= 0:
                await interaction.response.send_message("❌ Loan amount must be greater than 0.", ephemeral=True)
                return
            
            # Check for existing pending loans
            existing = await db.get_user_pending_loans(str(interaction.guild_id), str(interaction.user.id))
            if existing:
                embed = discord.Embed(
                    title="❌ Existing Loan Found",
                    description="You already have a pending or active loan.",
                    color=discord.Color.red()
                )
                embed.add_field(name="Existing Loan ID", value=f"`{existing[0]['loan_id']}`", inline=True)
                embed.add_field(name="Status", value=existing[0]['status'].title(), inline=True)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Get loan settings
            settings = await db.get_loan_settings(str(interaction.guild_id))
            max_amount = settings.get('max_loan_amount', 1000000) if settings else 1000000
            
            if amount > max_amount:
                await interaction.response.send_message(
                    f"❌ Loan amount exceeds maximum limit of {max_amount:,} UEC.",
                    ephemeral=True
                )
                return
            
            # Calculate interest (if applicable)
            interest_rate = float(settings.get('default_interest_rate', 0.05)) if settings else 0.05
            interest_amount = amount * interest_rate if interest_rate > 0 else 0
            total_repayment = amount + interest_amount
            
            # Create loan data
            loan_data = {
                'guild_id': str(interaction.guild_id),
                'borrower_id': str(interaction.user.id),
                'borrower_name': interaction.user.display_name,
                'amount': amount,
                'purpose': purpose,
                'repayment_plan': repayment_plan,
                'interest_rate': interest_rate,
                'interest_amount': interest_amount,
                'total_amount': total_repayment,
                'status': 'pending'
            }
            
            # Create confirmation embed
            embed = discord.Embed(
                title="💰 Loan Request Confirmation",
                description="Please review your loan request details:",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="Requested Amount", value=f"{amount:,} UEC", inline=True)
            if interest_amount > 0:
                embed.add_field(name="Interest", value=f"{interest_amount:,.2f} UEC ({interest_rate*100:.1f}%)", inline=True)
                embed.add_field(name="Total Repayment", value=f"{total_repayment:,.2f} UEC", inline=True)
            
            embed.add_field(name="Purpose", value=purpose, inline=False)
            
            if repayment_plan:
                embed.add_field(name="Repayment Plan", value=repayment_plan, inline=False)
            
            embed.add_field(
                name="⚠️ Important",
                value="• Loan approval is subject to officer review\n"
                      "• You are responsible for timely repayment\n"
                      "• Late payments may affect future loan eligibility",
                inline=False
            )
            
            embed.set_footer(text="Confirm to submit your loan request")
            
            # Create confirmation view
            view = LoanConfirmationView(loan_data)
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in loan request: {e}")
            await interaction.response.send_message(
                "❌ Error processing loan request. Please try again.",
                ephemeral=True
            )
    
    @app_commands.command(name='status', description='Check your loan status')
    async def loan_status(self, interaction: discord.Interaction):
        """Check the status of your loans"""
        try:
            from ..database.database import Database
            
            db = Database()
            loans = await db.get_user_loans(str(interaction.guild_id), str(interaction.user.id))
            
            if not loans:
                embed = discord.Embed(
                    title="💰 No Loans Found",
                    description="You don't have any loans on record.",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Request a Loan", value="Use `/redloans request` to apply for a loan", inline=False)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create status embed
            embed = discord.Embed(
                title="💰 Your Loans",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            for loan in loans:
                status_colors = {
                    'pending': '🟡',
                    'approved': '🟢',
                    'denied': '🔴',
                    'active': '🔵',
                    'completed': '✅',
                    'overdue': '⚠️'
                }
                
                status_emoji = status_colors.get(loan['status'], '⚪')
                
                value = f"**Amount:** {loan['amount']:,} UEC\n"
                value += f"**Status:** {status_emoji} {loan['status'].title()}\n"
                
                if loan['status'] == 'active':
                    remaining = loan['total_amount'] - loan.get('amount_paid', 0)
                    value += f"**Remaining:** {remaining:,.2f} UEC\n"
                    
                    if loan.get('due_date'):
                        due_date = datetime.fromisoformat(str(loan['due_date']))
                        value += f"**Due:** <t:{int(due_date.timestamp())}:D>\n"
                
                if loan.get('approved_by_name'):
                    value += f"**Approved by:** {loan['approved_by_name']}\n"
                
                value += f"**Purpose:** {loan['purpose']}"
                
                embed.add_field(
                    name=f"Loan #{loan['loan_id']}",
                    value=value,
                    inline=True
                )
            
            embed.set_footer(text="Red Legion Finance System")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in loan status: {e}")
            await interaction.response.send_message(
                "❌ Error retrieving loan status.",
                ephemeral=True
            )
    
    @app_commands.command(name='approve', description='[FINANCE] Approve a pending loan request')
    @app_commands.describe(loan_id='The ID of the loan to approve')
    async def approve_loan(self, interaction: discord.Interaction, loan_id: int):
        """Approve a pending loan request (finance officer command)"""
        try:
            # Check permissions
            if not any(role.name.lower() in ['finance officer', 'finance', 'admin', 'leadership'] for role in interaction.user.roles):
                await interaction.response.send_message("❌ You don't have permission to approve loans.", ephemeral=True)
                return
            
            from ..database.database import Database
            
            db = Database()
            
            # Get loan details
            loan = await db.get_loan_by_id(loan_id)
            if not loan or loan['guild_id'] != str(interaction.guild_id):
                await interaction.response.send_message("❌ Loan not found.", ephemeral=True)
                return
            
            if loan['status'] != 'pending':
                await interaction.response.send_message(f"❌ Loan is already {loan['status']}.", ephemeral=True)
                return
            
            # Approve the loan
            await db.approve_loan(
                loan_id,
                str(interaction.user.id),
                interaction.user.display_name
            )
            
            embed = discord.Embed(
                title="✅ Loan Approved",
                description=f"Loan #{loan_id} has been approved.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="Borrower", value=loan['borrower_name'], inline=True)
            embed.add_field(name="Amount", value=f"{loan['amount']:,} UEC", inline=True)
            embed.add_field(name="Approved By", value=interaction.user.display_name, inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Notify the borrower
            await self._notify_borrower(interaction, loan, 'approved')
            
        except Exception as e:
            logger.error(f"Error approving loan: {e}")
            await interaction.response.send_message(
                "❌ Error approving loan.",
                ephemeral=True
            )
    
    @app_commands.command(name='deny', description='[FINANCE] Deny a pending loan request')
    @app_commands.describe(
        loan_id='The ID of the loan to deny',
        reason='Reason for denial'
    )
    async def deny_loan(self, interaction: discord.Interaction, loan_id: int, reason: str):
        """Deny a pending loan request (finance officer command)"""
        try:
            # Check permissions
            if not any(role.name.lower() in ['finance officer', 'finance', 'admin', 'leadership'] for role in interaction.user.roles):
                await interaction.response.send_message("❌ You don't have permission to deny loans.", ephemeral=True)
                return
            
            from ..database.database import Database
            
            db = Database()
            
            # Get loan details
            loan = await db.get_loan_by_id(loan_id)
            if not loan or loan['guild_id'] != str(interaction.guild_id):
                await interaction.response.send_message("❌ Loan not found.", ephemeral=True)
                return
            
            if loan['status'] != 'pending':
                await interaction.response.send_message(f"❌ Loan is already {loan['status']}.", ephemeral=True)
                return
            
            # Deny the loan
            await db.deny_loan(
                loan_id,
                str(interaction.user.id),
                interaction.user.display_name,
                reason
            )
            
            embed = discord.Embed(
                title="❌ Loan Denied",
                description=f"Loan #{loan_id} has been denied.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="Borrower", value=loan['borrower_name'], inline=True)
            embed.add_field(name="Amount", value=f"{loan['amount']:,} UEC", inline=True)
            embed.add_field(name="Denied By", value=interaction.user.display_name, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Notify the borrower
            await self._notify_borrower(interaction, loan, 'denied', reason)
            
        except Exception as e:
            logger.error(f"Error denying loan: {e}")
            await interaction.response.send_message(
                "❌ Error denying loan.",
                ephemeral=True
            )
    
    @app_commands.command(name='pay', description='Record a loan payment')
    @app_commands.describe(
        loan_id='The ID of the loan to pay',
        amount='Payment amount in UEC'
    )
    async def pay_loan(self, interaction: discord.Interaction, loan_id: int, amount: float):
        """Record a loan payment"""
        try:
            from ..database.database import Database
            
            db = Database()
            
            # Get loan details
            loan = await db.get_loan_by_id(loan_id)
            if not loan or loan['guild_id'] != str(interaction.guild_id):
                await interaction.response.send_message("❌ Loan not found.", ephemeral=True)
                return
            
            # Check if user is borrower or finance officer
            is_borrower = loan['borrower_id'] == str(interaction.user.id)
            is_finance = any(role.name.lower() in ['finance officer', 'finance', 'admin', 'leadership'] for role in interaction.user.roles)
            
            if not (is_borrower or is_finance):
                await interaction.response.send_message("❌ You can only pay your own loans.", ephemeral=True)
                return
            
            if loan['status'] != 'active':
                await interaction.response.send_message(f"❌ Loan is not active (status: {loan['status']}).", ephemeral=True)
                return
            
            if amount <= 0:
                await interaction.response.send_message("❌ Payment amount must be greater than 0.", ephemeral=True)
                return
            
            # Calculate remaining balance
            remaining = loan['total_amount'] - loan.get('amount_paid', 0)
            
            if amount > remaining:
                await interaction.response.send_message(
                    f"❌ Payment amount ({amount:,.2f} UEC) exceeds remaining balance ({remaining:,.2f} UEC).",
                    ephemeral=True
                )
                return
            
            # Record the payment
            await db.record_loan_payment(
                loan_id,
                str(interaction.user.id),
                interaction.user.display_name,
                amount
            )
            
            new_remaining = remaining - amount
            is_complete = new_remaining <= 0.01  # Account for floating point precision
            
            embed = discord.Embed(
                title="💰 Payment Recorded",
                description=f"Payment of {amount:,.2f} UEC recorded for Loan #{loan_id}",
                color=discord.Color.green() if is_complete else discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="Payment Amount", value=f"{amount:,.2f} UEC", inline=True)
            embed.add_field(name="Remaining Balance", value=f"{new_remaining:,.2f} UEC", inline=True)
            
            if is_complete:
                embed.add_field(name="Status", value="🎉 **LOAN COMPLETED!**", inline=True)
            
            embed.add_field(name="Recorded By", value=interaction.user.display_name, inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error recording payment: {e}")
            await interaction.response.send_message(
                "❌ Error recording payment.",
                ephemeral=True
            )
    
    @app_commands.command(name='list', description='[FINANCE] List all loans')
    @app_commands.describe(status='Filter by loan status')
    @app_commands.choices(status=[
        app_commands.Choice(name='Pending', value='pending'),
        app_commands.Choice(name='Active', value='active'),
        app_commands.Choice(name='Completed', value='completed'),
        app_commands.Choice(name='Overdue', value='overdue'),
        app_commands.Choice(name='All', value='all')
    ])
    async def list_loans(self, interaction: discord.Interaction, status: app_commands.Choice[str] = None):
        """List all loans (finance officer command)"""
        try:
            # Check permissions
            if not any(role.name.lower() in ['finance officer', 'finance', 'admin', 'leadership'] for role in interaction.user.roles):
                await interaction.response.send_message("❌ You don't have permission to list loans.", ephemeral=True)
                return
            
            from ..database.database import Database
            
            db = Database()
            
            filter_status = status.value if status and status.value != 'all' else None
            loans = await db.get_loans_list(str(interaction.guild_id), filter_status)
            
            if not loans:
                embed = discord.Embed(
                    title="💰 Loans List",
                    description="No loans found matching the criteria.",
                    color=discord.Color.blue()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create paginated embed
            embed = discord.Embed(
                title="💰 Organization Loans",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            if filter_status:
                embed.description = f"**Filter:** {filter_status.title()} loans"
            
            # Add loans (limit to first 10)
            for loan in loans[:10]:
                status_emoji = {
                    'pending': '🟡',
                    'approved': '🟢',
                    'denied': '🔴',
                    'active': '🔵',
                    'completed': '✅',
                    'overdue': '⚠️'
                }.get(loan['status'], '⚪')
                
                value = f"**Amount:** {loan['amount']:,} UEC\n"
                value += f"**Status:** {status_emoji} {loan['status'].title()}\n"
                
                if loan['status'] == 'active':
                    remaining = loan['total_amount'] - loan.get('amount_paid', 0)
                    value += f"**Remaining:** {remaining:,.2f} UEC\n"
                
                value += f"**Purpose:** {loan['purpose'][:50]}..."
                
                embed.add_field(
                    name=f"#{loan['loan_id']} - {loan['borrower_name']}",
                    value=value,
                    inline=True
                )
            
            if len(loans) > 10:
                embed.set_footer(text=f"Showing 10 of {len(loans)} loans")
            else:
                embed.set_footer(text=f"Total: {len(loans)} loans")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error listing loans: {e}")
            await interaction.response.send_message(
                "❌ Error retrieving loans list.",
                ephemeral=True
            )
    
    async def _notify_borrower(self, interaction: discord.Interaction, loan: dict, action: str, reason: str = None):
        """Notify borrower of loan status change"""
        try:
            borrower = interaction.guild.get_member(int(loan['borrower_id']))
            if not borrower:
                return
            
            if action == 'approved':
                embed = discord.Embed(
                    title="✅ Loan Approved!",
                    description=f"Your loan request has been approved.",
                    color=discord.Color.green()
                )
                embed.add_field(name="Loan ID", value=f"#{loan['loan_id']}", inline=True)
                embed.add_field(name="Amount", value=f"{loan['amount']:,} UEC", inline=True)
                embed.add_field(
                    name="Next Steps",
                    value="Coordinate with finance officers for fund transfer.",
                    inline=False
                )
            else:  # denied
                embed = discord.Embed(
                    title="❌ Loan Request Denied",
                    description=f"Your loan request has been denied.",
                    color=discord.Color.red()
                )
                embed.add_field(name="Loan ID", value=f"#{loan['loan_id']}", inline=True)
                embed.add_field(name="Amount", value=f"{loan['amount']:,} UEC", inline=True)
                if reason:
                    embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(
                    name="Reapplication",
                    value="You may submit a new loan request at any time.",
                    inline=False
                )
            
            await borrower.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error notifying borrower: {e}")

class LoanManagement(commands.Cog):
    """Loan Management Cog using Discord subcommand groups."""
    
    def __init__(self, bot):
        self.bot = bot
    
    # Properly register the command group
    redloans = RedLoansGroup()


async def setup(bot):
    """Setup function for discord.py extension loading."""
    print("🔧 Setting up Loan Management with subcommand groups...")
    try:
        cog = LoanManagement(bot)
        await bot.add_cog(cog)
        print("✅ Loan Management cog loaded with subcommand groups")
        print("✅ Available commands:")
        print("   • /redloans request <amount> [reason]")
        print("   • /redloans status")
        print("   • /redloans list")
    except Exception as e:
        print(f"❌ Error in setup function: {e}")
        import traceback
        traceback.print_exc()