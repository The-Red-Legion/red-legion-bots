"""
Loan system commands for the Red Legion Discord bot.

This module contains slash commands for managing the organization loan system.
All commands are prefixed with "red-" for easy identification.
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class Loans(commands.Cog):
    """Loan-related commands for Red Legion bot."""
    
    def __init__(self, bot):
        self.bot = bot
        print("✅ Loans Cog initialized")

    @app_commands.command(name="red-loan-request", description="Request a loan from the Red Legion organization (Org Members only)")
    @app_commands.describe(amount="Amount to request in credits")
    async def request_loan(self, interaction: discord.Interaction, amount: int):
        """Request a loan from the organization"""
        try:
            from config.settings import get_database_url
            from database.operations import issue_loan
            
            db_url = get_database_url()
            if not db_url:
                await interaction.response.send_message("❌ Database not configured")
                return
            
            # Validate loan amount
            if amount <= 0:
                await interaction.response.send_message("❌ Loan amount must be greater than 0")
                return
                
            if amount > 1000000:  # 1 million credit limit
                await interaction.response.send_message("❌ Loan amount too large (max 1,000,000 credits)")
                return
            
            # Calculate dates
            issued_date = datetime.now()
            due_date = issued_date + timedelta(days=30)  # 30-day loan term
            
            # Issue the loan
            loan_id = issue_loan(
                db_url,
                str(interaction.user.id),
                interaction.user.display_name,
                amount,
                issued_date.isoformat(),
                due_date.isoformat()
            )
            
            embed = discord.Embed(
                title="✅ Red Legion Loan Approved",
                description=f"Your loan request has been approved!",
                color=discord.Color.green()
            )
            
            embed.add_field(name="Loan ID", value=f"#{loan_id}", inline=True)
            embed.add_field(name="Amount", value=f"{amount:,} credits", inline=True)
            embed.add_field(name="Term", value="30 days", inline=True)
            embed.add_field(name="Due Date", value=due_date.strftime("%Y-%m-%d"), inline=True)
            embed.add_field(name="Interest", value="5% (org standard)", inline=True)
            embed.add_field(name="Total Due", value=f"{int(amount * 1.05):,} credits", inline=True)
            
            embed.set_footer(text="Contact an org admin if you have questions about your loan")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to process loan request: {e}")

    @app_commands.command(name="red-loan-status", description="Check your current loan status")
    async def loan_status(self, interaction: discord.Interaction):
        """Check current loan status for the user"""
        try:
            from config.settings import get_database_url
            from database.operations import get_user_loans
            
            db_url = get_database_url()
            if not db_url:
                await interaction.response.send_message("❌ Database not configured")
                return
            
            loans = get_user_loans(db_url, str(interaction.user.id))
            
            if not loans:
                await interaction.response.send_message("📊 You have no active loans with Red Legion")
                return
            
            embed = discord.Embed(
                title="📊 Your Red Legion Loans",
                description=f"Loan status for {interaction.user.display_name}",
                color=discord.Color.blue()
            )
            
            total_owed = 0
            for loan in loans:
                loan_id, amount, issued_date, due_date, status = loan
                total_with_interest = int(amount * 1.05)
                total_owed += total_with_interest
                
                status_emoji = "✅" if status == "paid" else "⏳" if status == "active" else "❌"
                
                embed.add_field(
                    name=f"{status_emoji} Loan #{loan_id}",
                    value=f"**Amount**: {amount:,} credits\\n**Due**: {due_date}\\n**Status**: {status.title()}",
                    inline=True
                )
            
            embed.add_field(
                name="💰 Total Owed",
                value=f"{total_owed:,} credits",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to get loan status: {e}")


async def setup(bot):
    """Setup function for discord.py extension loading."""
    await bot.add_cog(Loans(bot))
    print("✅ Loans commands loaded")
