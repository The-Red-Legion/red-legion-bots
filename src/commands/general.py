"""
General purpose commands for the Red Legion Discord bot.

This module contains basic bot commands and utilities.
All commands are prefixed with "red-" for easy identification.
"""

import discord
from discord.ext import commands
from discord import app_commands
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class General(commands.Cog):
    """General purpose commands for Red Legion bot."""
    
    def __init__(self, bot):
        self.bot = bot
        print("✅ General Cog initialized")

    @app_commands.command(name="red-ping", description="Test Red Legion bot responsiveness")
    async def ping_cmd(self, interaction: discord.Interaction):
        """Simple ping command to test bot responsiveness"""
        latency_ms = round(self.bot.latency * 1000, 2)
        
        embed = discord.Embed(
            title="🏓 Red Legion Pong!",
            description="Bot is responding normally",
            color=discord.Color.green()
        )
        embed.add_field(name="Latency", value=f"{latency_ms}ms", inline=True)
        embed.add_field(name="Status", value="✅ Online", inline=True)
        
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    """Setup function for discord.py extension loading."""
    await bot.add_cog(General(bot))
    print("✅ General commands loaded")
