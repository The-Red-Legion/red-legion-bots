"""
General purpose commands for the Red Legion Discord bot.

This module contains basic bot commands and utilities.
"""

import discord
from discord.ext import commands
from ..core.decorators import error_handler


def register_commands(bot):
    """Register all general commands with the bot."""
    
    @bot.command(name="ping")
    @error_handler
    async def ping_cmd(ctx):
        """Simple ping command to test bot responsiveness"""
        latency_ms = round(bot.latency * 1000, 2)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Bot is responding normally",
            color=discord.Color.green()
        )
        embed.add_field(name="Latency", value=f"{latency_ms}ms", inline=True)
        embed.add_field(name="Status", value="✅ Online", inline=True)
        
        await ctx.send(embed=embed)

    print("✅ General commands registered")
