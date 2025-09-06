"""
Administrative commands for the Red Legion Discord bot.

This module contains commands for bot administration and configuration management.
"""

import discord
from discord.ext import commands
from datetime import datetime
import os
import sys
from ..core.decorators import has_org_role, admin_only, error_handler


def register_commands(bot):
    """Register all administrative commands with the bot."""
    
    @bot.command(name="refresh_config")
    @admin_only()
    @error_handler
    async def refresh_config(ctx):
        """Refresh bot configuration from Secret Manager"""
        try:
            embed = discord.Embed(
                title="🔄 Configuration Refresh",
                description="Refreshing configuration from Secret Manager...",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            # Send initial message
            msg = await ctx.send(embed=embed)
            
            # Attempt to refresh configuration
            try:
                from ..config import get_config
                
                # Get fresh config
                new_config = get_config()
                
                # Update embed with success
                embed.title = "✅ Configuration Refreshed"
                embed.description = "Configuration successfully refreshed from Secret Manager"
                embed.color = discord.Color.green()
                
                # Add status fields
                embed.add_field(
                    name="Database URL", 
                    value="✅ Updated" if new_config.get('DATABASE_URL') else "❌ Not found", 
                    inline=True
                )
                embed.add_field(
                    name="Discord Token", 
                    value="✅ Available" if new_config.get('DISCORD_TOKEN') else "❌ Not found", 
                    inline=True
                )
                
                await msg.edit(embed=embed)
                
            except Exception as config_error:
                embed.title = "❌ Configuration Refresh Failed"
                embed.description = f"Failed to refresh configuration: {str(config_error)}"
                embed.color = discord.Color.red()
                embed.add_field(
                    name="Error Details",
                    value=str(config_error)[:100],
                    inline=False
                )
                await msg.edit(embed=embed)
                
        except Exception as e:
            await ctx.send(f"❌ Failed to refresh configuration: {str(e)}")

    @bot.command(name="restart_red_legion_bot")
    @admin_only()
    @error_handler
    async def restart_bot(ctx):
        """Restart the bot process (admin only)"""
        try:
            # Create confirmation embed
            embed = discord.Embed(
                title="🔄 Bot Restart Initiated",
                description="Restarting the Red Legion bot...",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            embed.add_field(
                name="Initiated By",
                value=f"{ctx.author.mention} ({ctx.author.id})",
                inline=False
            )
            embed.add_field(
                name="Status",
                value="Bot will restart momentarily",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
            # Give time for the message to send before restarting
            import asyncio
            await asyncio.sleep(2)
            
            # Log the restart
            print(f"Bot restart initiated by {ctx.author} ({ctx.author.id})")
            
            # Restart the bot process
            os.execv(sys.executable, ['python'] + sys.argv)
            
        except Exception as e:
            await ctx.send(f"❌ Failed to restart bot: {str(e)}")

    print("✅ Admin commands registered")
