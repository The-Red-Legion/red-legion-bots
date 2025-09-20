"""
Admin Commands for Red Legion Bot

Administrative commands for managing events, users, and bot operations.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List, Dict
import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import get_cursor
from config.settings import UEX_API_CONFIG


class AdminCommands(commands.GroupCog, name="admin", description="Administrative commands (Admin only)"):
    """Administrative commands group."""
    
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
    
    # DEPRECATED: delete-event command moved to Management Portal

    @app_commands.command(name="voice-diagnostic", description="Diagnose voice channel connectivity issues")
    @app_commands.default_permissions(administrator=True)
    async def voice_diagnostic(self, interaction: discord.Interaction):
        """Comprehensive voice channel diagnostic test."""
        await interaction.response.defer(ephemeral=True)
    
        try:
            guild = interaction.guild
            bot_member = guild.get_member(self.bot.user.id)
        
            # Create diagnostic embed
            embed = discord.Embed(
                title="🔧 Voice Channel Diagnostic Report",
                description="Testing bot voice capabilities and channel configurations",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
        
            # 1. Bot Permissions Check
            permissions_info = []
            guild_perms = bot_member.guild_permissions
            permissions_info.append(f"Connect: {'✅' if guild_perms.connect else '❌'}")
            permissions_info.append(f"Speak: {'✅' if guild_perms.speak else '❌'}")
            permissions_info.append(f"Use Voice Activity: {'✅' if guild_perms.use_voice_activation else '❌'}")
            permissions_info.append(f"View Channels: {'✅' if guild_perms.view_channel else '❌'}")
            permissions_info.append(f"Administrator: {'✅' if guild_perms.administrator else '❌'}")
        
            embed.add_field(
                name="🛡️ Bot Guild Permissions",
                value="\n".join(permissions_info),
                inline=True
            )
        
            # 2. Check Mining Channels Configuration
            try:
                from config.settings import get_sunday_mining_channels, SUNDAY_MINING_CHANNELS_FALLBACK
            
                # Try database lookup with fallback if it hangs/fails
                try:
                    channels_config = get_sunday_mining_channels(guild.id)
                except Exception as db_error:
                    print(f"Database lookup failed, using fallback: {db_error}")
                    channels_config = SUNDAY_MINING_CHANNELS_FALLBACK
            
                channel_status = []
                dispatch_channel = None
                voice_channels = []
            
                if channels_config:
                    # Check dispatch channel
                    if 'dispatch' in channels_config:
                        dispatch_id = int(channels_config['dispatch'])
                        dispatch_channel = guild.get_channel(dispatch_id)
                        if dispatch_channel:
                            channel_status.append(f"📢 Dispatch: `{dispatch_channel.name}` ✅")
                        else:
                            channel_status.append(f"📢 Dispatch: ID `{dispatch_id}` ❌ Not Found")
                
                    # Check voice channels (all non-dispatch channels)
                    voice_channel_configs = {k: v for k, v in channels_config.items() if k != 'dispatch'}
                    for channel_name, vc_id_str in voice_channel_configs.items():
                        try:
                            vc_id = int(vc_id_str)
                            vc = guild.get_channel(vc_id)
                            if vc:
                                # Check bot permissions in this specific channel
                                vc_perms = vc.permissions_for(bot_member)
                                perm_status = "✅" if (vc_perms.connect and vc_perms.view_channel) else "❌"
                                channel_status.append(f"🎤 Voice: `{vc.name}` {perm_status}")
                                voice_channels.append((vc, vc_perms))
                            else:
                                channel_status.append(f"🎤 Voice: ID `{vc_id}` ❌ Not Found")
                        except (ValueError, TypeError):
                            channel_status.append(f"🎤 Voice: `{channel_name}` ❌ Invalid ID")
                else:
                    channel_status.append("❌ No mining channels configured")
            
                embed.add_field(
                    name="📋 Channel Configuration",
                    value="\n".join(channel_status) if channel_status else "No channels found",
                    inline=True
                )
            
                # 3. Test Voice Connection
                connection_tests = []
            
                if voice_channels:
                    for vc, perms in voice_channels[:2]:  # Test first 2 channels
                        try:
                            # Check if we can theoretically connect
                            if perms.connect and perms.view_channel:
                                # Try to get voice client info
                                if vc.guild.voice_client:
                                    if vc.guild.voice_client.channel == vc:
                                        connection_tests.append(f"🟢 `{vc.name}`: Already connected")
                                    else:
                                        connection_tests.append(f"🟡 `{vc.name}`: Connected elsewhere")
                                else:
                                    connection_tests.append(f"🔵 `{vc.name}`: Ready to connect")
                                
                                # Check user limit
                                if vc.user_limit > 0:
                                    current_users = len(vc.members)
                                    if current_users >= vc.user_limit:
                                        connection_tests.append(f"⚠️ `{vc.name}`: Channel full ({current_users}/{vc.user_limit})")
                                    else:
                                        connection_tests.append(f"👥 `{vc.name}`: Space available ({current_users}/{vc.user_limit})")
                                else:
                                    connection_tests.append(f"👥 `{vc.name}`: No user limit")
                            else:
                                missing_perms = []
                                if not perms.connect: missing_perms.append("Connect")
                                if not perms.view_channel: missing_perms.append("View")
                                connection_tests.append(f"❌ `{vc.name}`: Missing {', '.join(missing_perms)}")
                            
                        except Exception as e:
                            connection_tests.append(f"💥 `{vc.name}`: Error - {str(e)[:50]}")
            
                embed.add_field(
                    name="🔗 Voice Connection Tests",
                    value="\n".join(connection_tests) if connection_tests else "No voice channels to test",
                    inline=False
                )
            
                # 4. Current Voice State
                voice_state_info = []
                voice_client = guild.voice_client
            
                if voice_client:
                    voice_state_info.append(f"Connected: ✅ `{voice_client.channel.name}`")
                    voice_state_info.append(f"Latency: {voice_client.latency:.2f}ms")
                    voice_state_info.append(f"Is Connected: {'✅' if voice_client.is_connected() else '❌'}")
                else:
                    voice_state_info.append("Connected: ❌ Not in any channel")
            
                embed.add_field(
                    name="🎵 Current Voice State",
                    value="\n".join(voice_state_info),
                    inline=True
                )
            
                # 5. Recommendations
                recommendations = []
            
                if not guild_perms.connect:
                    recommendations.append("🔧 Grant bot 'Connect' permission")
                if not guild_perms.view_channel:
                    recommendations.append("🔧 Grant bot 'View Channels' permission")
                if not channels_config:
                    recommendations.append("🔧 Configure mining channels in settings")
                if dispatch_channel is None and channels_config and 'dispatch_channel_id' in channels_config:
                    recommendations.append("🔧 Fix dispatch channel configuration")
            
                for vc, perms in voice_channels:
                    if not perms.connect:
                        recommendations.append(f"🔧 Grant connect permission in `{vc.name}`")
            
                if not recommendations:
                    recommendations.append("✅ All configurations look good!")
            
                embed.add_field(
                    name="💡 Recommendations",
                    value="\n".join(recommendations[:5]),  # Limit to 5 recommendations
                    inline=False
                )
            
                # Add footer with debug info
                embed.set_footer(text=f"Guild ID: {guild.id} | Bot ID: {self.bot.user.id}")
            
            except Exception as config_error:
                embed.add_field(
                    name="❌ Configuration Error",
                    value=f"Could not load channel config: {str(config_error)}",
                    inline=False
                )
        
            await interaction.followup.send(embed=embed, ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(
                f"❌ Diagnostic failed: {str(e)}",
                ephemeral=True
            )

    # DEPRECATED: fix-event-durations command moved to Management Portal

    @app_commands.command(name="test-uex-api", description="Test UEX API connection and bearer token")
    @app_commands.default_permissions(administrator=True)
    async def test_uex_api(self, interaction: discord.Interaction):
        """Test UEX API to verify bearer token and connection."""
        # Check admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ This command requires administrator permissions.",
                ephemeral=True
            )
            return
    
        await interaction.response.defer(ephemeral=True)
    
        try:
            from modules.payroll.processors.mining import MiningProcessor
            processor = MiningProcessor()
        
            # Test UEX API call
            prices = await processor.get_current_prices(refresh=True)  # Force refresh from API
        
            embed = discord.Embed(
                title="🧪 UEX API Test Results",
                color=discord.Color.green() if prices else discord.Color.red()
            )
        
            if prices:
                embed.description = f"✅ **UEX API connection successful!**\n\nRetrieved {len(prices)} ore prices."
            
                # Show sample prices
                sample_ores = list(prices.items())[:5]
                if sample_ores:
                    price_text = []
                    for ore_name, price_data in sample_ores:
                        price = price_data.get('price', 0)
                        location = price_data.get('location', 'Unknown')
                        price_text.append(f"**{ore_name}**: {price:,.0f} aUEC ({location})")
                
                    embed.add_field(
                        name="📊 Sample Prices",
                        value="\n".join(price_text),
                        inline=False
                    )
            
                embed.add_field(
                    name="🔧 Configuration",
                    value=f"API URL: `{UEX_API_CONFIG['base_url']}`\n"
                          f"Bearer Token: `{UEX_API_CONFIG['bearer_token'][:10]}...`\n"
                          f"Timeout: {UEX_API_CONFIG['timeout']}s",
                    inline=False
                )
            else:
                embed.description = "❌ **UEX API connection failed!**\n\nNo price data retrieved."
                embed.add_field(
                    name="🔧 Configuration",
                    value=f"API URL: `{UEX_API_CONFIG['base_url']}`\n"
                          f"Bearer Token: `{UEX_API_CONFIG['bearer_token'][:10]}...`\n"
                          f"Timeout: {UEX_API_CONFIG['timeout']}s",
                    inline=False
                )
                embed.add_field(
                    name="🔍 Next Steps",
                    value="• Check bot logs for detailed error messages\n"
                          "• Verify bearer token is still valid\n"
                          "• Check UEX Corp API status",
                    inline=False
                )
        
            await interaction.followup.send(embed=embed, ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error Testing UEX API",
                    description=f"An unexpected error occurred: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

    @app_commands.command(name="restart", description="Restart the Red Legion bot service (Admin only)")
    @app_commands.default_permissions(administrator=True)
    async def restart_bot(self, interaction: discord.Interaction):
        """Restart the bot service (admin only)."""
        try:
            # Check admin permissions
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "❌ This command requires administrator permissions.",
                    ephemeral=True
                )
                return
        
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="🔄 Restarting Bot",
                    description="Bot restart initiated by admin. The bot will be back online shortly.",
                    color=discord.Color.orange()
                ),
                ephemeral=False  # Let everyone see the restart notification
            )
        
            # Import here to avoid circular imports
            import os
            import sys
        
            # Attempt to restart via systemctl if on Linux/VM
            try:
                import subprocess
                result = subprocess.run(
                    ["sudo", "systemctl", "restart", "red-legion-bot"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if result.returncode == 0:
                    # This message likely won't be sent since bot is restarting
                    await interaction.followup.send("✅ Bot restart command sent to system service.")
                else:
                    # Fall back to Python exit restart
                    await interaction.followup.send("⚠️ System restart failed, attempting Python restart...")
                    await self.bot.close()
                    os.execv(sys.executable, ['python'] + sys.argv)
            except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
                # Fall back to Python restart if systemctl is not available
                await interaction.followup.send("🔄 Performing Python restart...")
                await self.bot.close()
                os.execv(sys.executable, ['python'] + sys.argv)
            
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Restart Failed",
                    description=f"Failed to restart bot: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

    @app_commands.command(name="update-prices", description="Update UEX ore prices in database (Admin only)")
    @app_commands.default_permissions(administrator=True)
    async def update_uex_prices(self, interaction: discord.Interaction):
        """Update UEX ore prices in database."""
        try:
            # Check admin permissions
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "❌ This command requires administrator permissions.",
                    ephemeral=True
                )
                return
        
            await interaction.response.defer()
        
            # Import here to avoid circular imports
            from modules.payroll.processors.mining import MiningProcessor
        
            processor = MiningProcessor()
        
            await interaction.followup.send(
                embed=discord.Embed(
                    title="🔄 Updating UEX Ore Prices",
                    description="Fetching latest ore prices from UEX Corp API...",
                    color=discord.Color.blue()
                )
            )
        
            # Fetch prices from UEX
            ore_prices = await processor.get_current_prices(refresh=True)
        
            if ore_prices:
                # Create summary embed
                embed = discord.Embed(
                    title="✅ UEX Prices Updated Successfully",
                    description=f"Updated {len(ore_prices)} ore prices in database.",
                    color=discord.Color.green()
                )
            
                # Add sample prices
                price_sample = []
                count = 0
                for ore_name, price_data in ore_prices.items():
                    if count >= 8:  # Limit to avoid embed size limits
                        break
                    price_sample.append(f"• **{ore_name}:** {price_data['price']:,.0f} aUEC/SCU")
                    count += 1
            
                if len(ore_prices) > 8:
                    price_sample.append(f"... and {len(ore_prices) - 8} more ores")
            
                embed.add_field(
                    name="🏷️ Sample Prices",
                    value="\n".join(price_sample),
                    inline=False
                )
            
                embed.add_field(
                    name="ℹ️ Note",
                    value="These prices are now cached and will be used for payroll calculations.",
                    inline=False
                )
            
            else:
                embed = discord.Embed(
                    title="❌ UEX Price Update Failed",
                    description="Unable to fetch prices from UEX Corp API. Check logs for details.",
                    color=discord.Color.red()
                )
            
                embed.add_field(
                    name="🔧 Troubleshooting",
                    value="• Check bot logs for detailed error messages\n"
                          "• Verify UEX Corp API is accessible\n"
                          "• Ensure bearer token is still valid",
                    inline=False
                )
        
            await interaction.edit_original_response(embed=embed)
        
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error Updating Prices",
                    description=f"An unexpected error occurred: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )


async def setup(bot):
    """Setup function for discord.py extension loading."""
    await bot.add_cog(AdminCommands(bot))
