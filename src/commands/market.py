"""
Market-related commands for the Red Legion Discord bot.

This module contains slash commands for managing the organization market system.
All commands are prefixed with "red-" for easy identification.
"""

import discord
from discord.ext import commands
from discord import app_commands
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class Market(commands.Cog):
    """Market-related commands for Red Legion bot."""
    
    def __init__(self, bot):
        self.bot = bot
        print("✅ Market Cog initialized")

    @app_commands.command(name="red-market-list", description="List all items in the Red Legion market")
    async def list_market(self, interaction: discord.Interaction):
        """List all items available in the organization market"""
        try:
            from config.settings import get_database_url
            from database import get_market_items
            
            db_url = get_database_url()
            if not db_url:
                await interaction.response.send_message("❌ Database not configured")
                return
                
            items = get_market_items(db_url)
            
            if not items:
                await interaction.response.send_message("📦 Red Legion market is currently empty")
                return
            
            embed = discord.Embed(
                title="🏪 Red Legion Market",
                description="Available items for purchase",
                color=discord.Color.blue()
            )
            
            for item in items:
                _, item_name, price, stock = item
                embed.add_field(
                    name=f"📦 {item_name}",
                    value=f"**Price**: {price:,} credits\\n**Stock**: {stock}",
                    inline=True
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to list market items: {e}")

    @app_commands.command(name="red-market-add", description="Add a new item to the Red Legion market (Org Members only)")
    @app_commands.describe(
        name="Name of the item",
        price="Price in credits", 
        stock="Available quantity"
    )
    async def add_market_item_cmd(self, interaction: discord.Interaction, name: str, price: int, stock: int):
        """Add a new item to the organization market"""
        try:
            from config.settings import get_database_url
            from database import add_market_item
            
            db_url = get_database_url()
            if not db_url:
                await interaction.response.send_message("❌ Database not configured")
                return
            
            # Validate inputs
            if price <= 0:
                await interaction.response.send_message("❌ Price must be greater than 0")
                return
                
            if stock < 0:
                await interaction.response.send_message("❌ Stock cannot be negative")
                return
                
            if len(name) > 50:
                await interaction.response.send_message("❌ Item name too long (max 50 characters)")
                return
            
            add_market_item(db_url, name, price, stock)
            
            embed = discord.Embed(
                title="✅ Item Added to Red Legion Market",
                description=f"Successfully added **{name}** to the Red Legion market",
                color=discord.Color.green()
            )
            embed.add_field(name="Item Name", value=name, inline=True)
            embed.add_field(name="Price", value=f"{price:,} credits", inline=True)
            embed.add_field(name="Stock", value=stock, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to add market item: {e}")


async def setup(bot):
    """Setup function for discord.py extension loading."""
    await bot.add_cog(Market(bot))
    print("✅ Market commands loaded")
