"""
Diagnostic Commands for Red Legion Bot

Simple diagnostic tools for troubleshooting common issues.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class DiagnosticCommands(commands.GroupCog, name="diagnostics", description="Bot diagnostic tools"):
    """Simple diagnostic commands group."""
    
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
    
    @app_commands.command(name="voice", description="Quick voice channel connectivity test")
    async def voice_diagnostic(self, interaction: discord.Interaction):
        """Quick voice channel diagnostic."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            guild = interaction.guild
            bot_member = guild.get_member(self.bot.user.id)
            
            embed = discord.Embed(
                title="🎤 Quick Voice Diagnostic",
                description="Basic voice connectivity check",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            # Check basic permissions
            guild_perms = bot_member.guild_permissions
            perms_ok = guild_perms.connect and guild_perms.view_channel
            
            embed.add_field(
                name="🛡️ Bot Permissions",
                value=f"Connect: {'✅' if guild_perms.connect else '❌'}\n"
                      f"View Channels: {'✅' if guild_perms.view_channel else '❌'}\n"
                      f"Overall: {'✅ Ready' if perms_ok else '❌ Missing Permissions'}",
                inline=True
            )
            
            # Check current voice state
            voice_client = guild.voice_client
            if voice_client:
                embed.add_field(
                    name="🎵 Current State",
                    value=f"Connected to: `{voice_client.channel.name}`\n"
                          f"Status: {'✅ Active' if voice_client.is_connected() else '❌ Disconnected'}",
                    inline=True
                )
            else:
                embed.add_field(
                    name="🎵 Current State", 
                    value="❌ Not connected to any voice channel",
                    inline=True
                )
            
            # Check voice channels in guild
            voice_channels = [ch for ch in guild.voice_channels if ch.permissions_for(bot_member).connect]
            embed.add_field(
                name="📋 Available Channels",
                value=f"Found {len(voice_channels)} connectable voice channels" if voice_channels 
                      else "❌ No voice channels available for connection",
                inline=False
            )
            
            # Quick recommendation
            if not perms_ok:
                embed.add_field(
                    name="💡 Quick Fix",
                    value="Grant the bot 'Connect' and 'View Channels' permissions",
                    inline=False
                )
            elif not voice_channels:
                embed.add_field(
                    name="💡 Quick Fix", 
                    value="Check channel-specific permissions for the bot",
                    inline=False
                )
            else:
                embed.add_field(
                    name="✅ Status",
                    value="Basic voice connectivity looks good!",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Diagnostic error: {str(e)}", 
                ephemeral=True
            )
    
    @app_commands.command(name="channels", description="List and test mining channel configuration")
    async def channels_diagnostic(self, interaction: discord.Interaction):
        """Test mining channel configuration."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            guild = interaction.guild
            bot_member = guild.get_member(self.bot.user.id)
            
            embed = discord.Embed(
                title="📡 Mining Channels Diagnostic", 
                description="Testing mining channel configuration",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            # Try to get mining channels config
            try:
                from config.settings import get_sunday_mining_channels
                channels_config = get_sunday_mining_channels(guild.id)
                
                if channels_config:
                    # Test dispatch channel
                    dispatch_status = []
                    if 'dispatch_channel_id' in channels_config:
                        dispatch_id = channels_config['dispatch_channel_id']
                        dispatch_ch = guild.get_channel(dispatch_id)
                        if dispatch_ch:
                            perms = dispatch_ch.permissions_for(bot_member)
                            can_send = perms.send_messages and perms.view_channel
                            dispatch_status.append(f"Channel: `{dispatch_ch.name}` {'✅' if can_send else '❌'}")
                        else:
                            dispatch_status.append(f"Channel ID `{dispatch_id}`: ❌ Not Found")
                    else:
                        dispatch_status.append("❌ No dispatch channel configured")
                    
                    embed.add_field(
                        name="📢 Dispatch Channel",
                        value="\n".join(dispatch_status),
                        inline=False
                    )
                    
                    # Test voice channels
                    voice_status = []
                    if 'voice_channel_ids' in channels_config:
                        for i, vc_id in enumerate(channels_config['voice_channel_ids'][:5]):  # Limit to 5
                            vc = guild.get_channel(vc_id)
                            if vc:
                                perms = vc.permissions_for(bot_member)
                                can_connect = perms.connect and perms.view_channel
                                voice_status.append(f"`{vc.name}`: {'✅' if can_connect else '❌'}")
                            else:
                                voice_status.append(f"ID `{vc_id}`: ❌ Not Found")
                        
                        if len(channels_config['voice_channel_ids']) > 5:
                            voice_status.append(f"... and {len(channels_config['voice_channel_ids']) - 5} more")
                    else:
                        voice_status.append("❌ No voice channels configured")
                    
                    embed.add_field(
                        name="🎤 Voice Channels",
                        value="\n".join(voice_status),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="⚠️ Configuration Issue",
                        value="No mining channels configured for this server.\n"
                              "Mining operations may not work properly.",
                        inline=False
                    )
                    
            except Exception as config_error:
                embed.add_field(
                    name="❌ Configuration Error",
                    value=f"Error loading channels config: {str(config_error)[:100]}...",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Channels diagnostic error: {str(e)}",
                ephemeral=True
            )


async def setup(bot):
    """Setup function for discord.py extension loading."""
    await bot.add_cog(DiagnosticCommands(bot))