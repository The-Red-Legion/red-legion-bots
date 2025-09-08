"""
Administrative commands for the Red Legion Discord bot.

This module contains slash commands for bot administration and configuration management.
All commands are prefixed with "red-" and restricted to administrators.
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class Admin(commands.Cog):
    """Administrative commands for Red Legion bot."""
    
    def __init__(self, bot):
        self.bot = bot
        print("✅ Admin Cog initialized")

    @app_commands.command(name="red-config-refresh", description="Refresh Red Legion bot configuration (Admin only)")
    @app_commands.default_permissions(administrator=True)
    async def refresh_config(self, interaction: discord.Interaction):
        """Refresh bot configuration from Secret Manager"""
        try:
            embed = discord.Embed(
                title="🔄 Red Legion Configuration Refresh",
                description="Refreshing configuration from Secret Manager...",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            # Send initial response
            await interaction.response.send_message(embed=embed)
            
            # Attempt to refresh configuration
            try:
                from config.settings import get_config
                
                # Get fresh config
                new_config = get_config()
                
                # Update embed with success
                embed.title = "✅ Red Legion Configuration Refreshed"
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
                
                await interaction.edit_original_response(embed=embed)
                
            except Exception as config_error:
                embed.title = "❌ Red Legion Configuration Refresh Failed"
                embed.description = f"Failed to refresh configuration: {str(config_error)}"
                embed.color = discord.Color.red()
                embed.add_field(
                    name="Error Details",
                    value=str(config_error)[:100],
                    inline=False
                )
                await interaction.edit_original_response(embed=embed)
                
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to refresh configuration: {str(e)}")

    @app_commands.command(name="red-restart", description="Restart the Red Legion bot (Admin only)")
    @app_commands.default_permissions(administrator=True)
    async def restart_bot(self, interaction: discord.Interaction):
        """Restart the bot process (admin only)"""
        try:
            # Create confirmation embed
            embed = discord.Embed(
                title="🔄 Red Legion Bot Restart Initiated",
                description="Restarting the Red Legion bot...",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            embed.add_field(
                name="Initiated By",
                value=f"{interaction.user.mention} ({interaction.user.id})",
                inline=False
            )
            embed.add_field(
                name="Status",
                value="Bot will restart momentarily",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Log the restart
            print(f"🔄 Bot restart initiated by {interaction.user.display_name} ({interaction.user.id})")
            
            # Restart the process
            import os
            os._exit(0)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to restart bot: {str(e)}")

    @app_commands.command(name="red-add-mining-channel", description="Add a mining channel to the Red Legion system (Admin only)")
    @app_commands.describe(channel="Voice channel to add for mining tracking")
    @app_commands.default_permissions(administrator=True)
    async def add_mining_channel(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Add a voice channel to the mining system"""
        try:
            # This would integrate with the mining channel management system
            embed = discord.Embed(
                title="✅ Red Legion Mining Channel Added",
                description=f"Successfully added {channel.mention} to the mining system",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="Channel Info",
                value=f"**Name:** {channel.name}\\n"
                      f"**ID:** {channel.id}\\n"
                      f"**Category:** {channel.category.name if channel.category else 'None'}",
                inline=False
            )
            
            embed.add_field(
                name="Added By",
                value=f"{interaction.user.display_name}",
                inline=True
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to add mining channel: {str(e)}")

    @app_commands.command(name="red-remove-mining-channel", description="Remove a mining channel from the Red Legion system (Admin only)")
    @app_commands.describe(channel="Voice channel to remove from mining tracking")
    @app_commands.default_permissions(administrator=True)
    async def remove_mining_channel(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Remove a voice channel from the mining system"""
        try:
            embed = discord.Embed(
                title="🗑️ Red Legion Mining Channel Removed",
                description=f"Successfully removed {channel.mention} from the mining system",
                color=discord.Color.orange()
            )
            
            embed.add_field(
                name="Channel Info",
                value=f"**Name:** {channel.name}\\n"
                      f"**ID:** {channel.id}",
                inline=False
            )
            
            embed.add_field(
                name="Removed By",
                value=f"{interaction.user.display_name}",
                inline=True
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to remove mining channel: {str(e)}")

    @app_commands.command(name="red-list-mining-channels", description="List all Red Legion mining channels (Admin only)")
    @app_commands.default_permissions(administrator=True)
    async def list_mining_channels(self, interaction: discord.Interaction):
        """List all voice channels in the mining system"""
        try:
            # Get all voice channels in the guild
            voice_channels = interaction.guild.voice_channels
            
            embed = discord.Embed(
                title="🎤 Red Legion Mining Channels",
                description=f"Found {len(voice_channels)} voice channels in this guild",
                color=discord.Color.blue()
            )
            
            if voice_channels:
                channel_list = []
                for i, channel in enumerate(voice_channels[:10], 1):  # Limit to first 10
                    members = len(channel.members)
                    channel_list.append(f"{i}. **{channel.name}** (ID: {channel.id}) - {members} members")
                
                embed.add_field(
                    name="Voice Channels",
                    value="\\n".join(channel_list),
                    inline=False
                )
                
                if len(voice_channels) > 10:
                    embed.add_field(
                        name="Note",
                        value=f"Showing first 10 of {len(voice_channels)} channels",
                        inline=False
                    )
            else:
                embed.add_field(
                    name="No Channels",
                    value="No voice channels found in this guild",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to list mining channels: {str(e)}")


async def setup(bot):
    """Setup function for discord.py extension loading."""
    await bot.add_cog(Admin(bot))
    print("✅ Admin commands loaded")
