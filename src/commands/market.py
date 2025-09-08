"""
Market-related commands for the Red Legion Discord bot.

This module contains commands for managing the organization market system.
"""

import discord
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.decorators import has_org_role, standard_cooldown, error_handler
from database import get_market_items, add_market_item


def register_commands(bot):
    """Register all market commands with the bot."""
    
    @bot.command(name="list_market")
    @has_org_role()
    @standard_cooldown()
    @error_handler
    async def list_market(ctx):
        """List all items available in the organization market"""
        try:
            from config.settings import get_database_url
            
            db_url = get_database_url()
            if not db_url:
                await ctx.send("❌ Database not configured")
                return
                
            items = get_market_items(db_url)
            
            if not items:
                await ctx.send("📦 Market is currently empty")
                return
            
            embed = discord.Embed(
                title="🏪 Organization Market",
                description="Available items for purchase",
                color=discord.Color.blue()
            )
            
            for item in items:
                _, item_name, price, stock = item
                embed.add_field(
                    name=f"📦 {item_name}",
                    value=f"**Price**: {price} credits\n**Stock**: {stock}",
                    inline=True
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Failed to list market items: {e}")

    @bot.command(name="add_market_item")
    @has_org_role()
    @standard_cooldown()
    @error_handler
    async def add_market_item_cmd(ctx, name: str, price: int, stock: int):
        """
        Add a new item to the organization market.
        
        Args:
            name: Name of the item
            price: Price in credits
            stock: Available quantity
        """
        try:
            from config.settings import get_database_url
            
            db_url = get_database_url()
            if not db_url:
                await ctx.send("❌ Database not configured")
                return
            
            # Validate inputs
            if price <= 0:
                await ctx.send("❌ Price must be greater than 0")
                return
                
            if stock < 0:
                await ctx.send("❌ Stock cannot be negative")
                return
                
            if len(name) > 50:
                await ctx.send("❌ Item name too long (max 50 characters)")
                return
            
            add_market_item(db_url, name, price, stock)
            
            embed = discord.Embed(
                title="✅ Item Added to Market",
                description=f"Successfully added **{name}** to the organization market",
                color=discord.Color.green()
            )
            embed.add_field(name="Price", value=f"{price} credits", inline=True)
            embed.add_field(name="Stock", value=str(stock), inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Failed to add market item: {e}")

    print("✅ Market commands registered")


async def setup(bot):
    """Setup function for discord.py extension loading."""
    register_commands(bot)
