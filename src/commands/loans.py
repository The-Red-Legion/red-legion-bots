"""
Loan system commands for the Red Legion Discord bot.

This module contains commands for managing the organization loan system.
"""

import discord
from discord.ext import commands
from datetime import datetime, timedelta
from ..core.decorators import has_org_role, standard_cooldown, error_handler
from ..database import issue_loan


def register_commands(bot):
    """Register all loan commands with the bot."""
    
    @bot.command(name="request_loan")
    @has_org_role()
    @standard_cooldown()
    @error_handler
    async def request_loan(ctx, amount: int):
        """
        Request a loan from the organization.
        
        Args:
            amount: Amount to request in credits
        """
        try:
            from ..config import get_database_url
            
            db_url = get_database_url()
            if not db_url:
                await ctx.send("❌ Database not configured")
                return
            
            # Validate loan amount
            if amount <= 0:
                await ctx.send("❌ Loan amount must be greater than 0")
                return
                
            if amount > 1000000:  # 1 million credit limit
                await ctx.send("❌ Loan amount too large (max 1,000,000 credits)")
                return
            
            # Calculate dates
            issued_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
            
            # Issue the loan
            issue_loan(db_url, ctx.author.id, amount, issued_date, due_date)
            
            # Create confirmation embed
            embed = discord.Embed(
                title="💰 Loan Request Submitted",
                description=f"Loan request for **{amount:,} credits** has been submitted",
                color=discord.Color.green()
            )
            embed.add_field(name="Requestor", value=ctx.author.mention, inline=True)
            embed.add_field(name="Amount", value=f"{amount:,} credits", inline=True)
            embed.add_field(name="Due Date", value=due_date.split()[0], inline=True)  # Just the date part
            embed.add_field(
                name="Terms", 
                value="30-day repayment period\nContact leadership for approval", 
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Failed to request loan: {e}")

    print("✅ Loan commands registered")
