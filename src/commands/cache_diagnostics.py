"""
Cache Diagnostics Module for Red Legion Discord Bot

Provides diagnostic commands for monitoring the UEX API cache system:
- Cache status and statistics
- Manual cache refresh
- Cache clearing for testing

Commands:
- /redcachestatus: Display cache status and statistics
- /redcacherefresh: Force refresh of cached data  
- /redcacheclear: Clear all cached data (admin only)
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, Any
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import can_manage_server


class CacheDiagnostics(commands.Cog):
    """Cache diagnostic commands for monitoring UEX API cache."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("📊 Cache diagnostics module loaded")

    @app_commands.command(name="redcachestatus", description="Show UEX cache status and statistics")
    async def cache_status(self, interaction: discord.Interaction):
        """Display UEX cache status and statistics."""
        await interaction.response.defer()
        
        try:
            from services.uex_cache import get_uex_cache
            
            cache = get_uex_cache()
            stats = cache.get_cache_stats()
            
            embed = discord.Embed(
                title="🗄️ UEX API Cache Status",
                color=discord.Color.blue(),
                description="Current status of the UEX price data cache system"
            )
            
            # Overall status
            status_emoji = "✅" if stats["running"] else "❌"
            embed.add_field(
                name="📊 Cache Service Status",
                value=f"{status_emoji} {'Running' if stats['running'] else 'Stopped'}\n"
                      f"📦 Cache Entries: {stats['cache_entries']}",
                inline=False
            )
            
            # Individual cache entries
            if stats["entries"]:
                cache_info = []
                for key, entry_stats in stats["entries"].items():
                    age_minutes = entry_stats["age_seconds"] / 60
                    validity_emoji = "✅" if entry_stats["valid"] else "⚠️"
                    
                    cache_info.append(
                        f"{validity_emoji} **{key}**\n"
                        f"   Age: {age_minutes:.1f} minutes\n"
                        f"   Items: {entry_stats['item_count']}\n"
                        f"   Valid: {'Yes' if entry_stats['valid'] else 'No'}"
                    )
                
                embed.add_field(
                    name="📋 Cache Entries",
                    value="\n\n".join(cache_info) if cache_info else "No cache entries",
                    inline=False
                )
            else:
                embed.add_field(
                    name="📋 Cache Entries",
                    value="No data cached yet",
                    inline=False
                )
            
            embed.set_footer(text="Cache TTL: 5 minutes • Refresh interval: 4 minutes")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Cache Status Error",
                description=f"Failed to retrieve cache status: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    @app_commands.command(name="redcacherefresh", description="Force refresh of UEX cache data")
    async def cache_refresh(self, interaction: discord.Interaction):
        """Force refresh all cached UEX data."""
        # Check permissions
        if not can_manage_server(interaction.user):
            await interaction.response.send_message(
                "❌ You don't have permission to refresh the cache",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            from services.uex_cache import get_uex_cache
            
            cache = get_uex_cache()
            
            # Force refresh all categories
            categories = ["ores", "high_value", "all"]
            results = {}
            
            for category in categories:
                try:
                    prices = await cache.get_ore_prices(category=category, force_refresh=True)
                    results[category] = len(prices) if prices else 0
                except Exception as e:
                    results[category] = f"Error: {str(e)}"
            
            embed = discord.Embed(
                title="🔄 Cache Refresh Complete",
                color=discord.Color.green(),
                description="Forced refresh of all cached UEX price data"
            )
            
            refresh_info = []
            for category, result in results.items():
                if isinstance(result, int):
                    refresh_info.append(f"✅ **{category}**: {result} items refreshed")
                else:
                    refresh_info.append(f"❌ **{category}**: {result}")
            
            embed.add_field(
                name="📊 Refresh Results",
                value="\n".join(refresh_info),
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Cache Refresh Error",
                description=f"Failed to refresh cache: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    @app_commands.command(name="redcacheclear", description="Clear all cached data (admin only)")
    async def cache_clear(self, interaction: discord.Interaction):
        """Clear all cached UEX data."""
        # Check permissions
        if not can_manage_server(interaction.user):
            await interaction.response.send_message(
                "❌ You don't have permission to clear the cache",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            from services.uex_cache import get_uex_cache
            
            cache = get_uex_cache()
            cache.clear_cache()
            
            embed = discord.Embed(
                title="🗑️ Cache Cleared",
                description="All cached UEX price data has been cleared.\n"
                           "Cache will automatically refill on next refresh cycle.",
                color=discord.Color.orange()
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Cache Clear Error",
                description=f"Failed to clear cache: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Load the Cache Diagnostics cog."""
    await bot.add_cog(CacheDiagnostics(bot))
    print("✅ Cache diagnostics commands loaded")