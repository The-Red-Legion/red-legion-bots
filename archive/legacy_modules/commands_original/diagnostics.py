"""
Diagnostic and health check commands for the Red Legion Discord bot.

This module contains slash commands for monitoring bot health, testing connectivity,
and checking configuration status. All commands are prefixed with "red-" for easy identification.
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class Diagnostics(commands.Cog):
    """Diagnostic and health check commands for Red Legion bot."""
    
    def __init__(self, bot):
        self.bot = bot
        print("✅ Diagnostics Cog initialized")

    @app_commands.command(name="redhealth", description="Simple health check for Red Legion bot monitoring")
    async def health_check(self, interaction: discord.Interaction):
        """Simple health check command for monitoring"""
        try:
            # Basic bot status
            uptime = datetime.now() - self.bot.start_time if hasattr(self.bot, 'start_time') else 'Unknown'
            guild_count = len(self.bot.guilds)
            
            # System status
            try:
                import psutil
                process = psutil.Process(os.getpid())
                memory_mb = process.memory_info().rss / 1024 / 1024
                memory_str = f"{round(memory_mb, 2)} MB"
            except ImportError:
                memory_str = "psutil not available"
            except Exception as e:
                memory_str = f"Error: {str(e)[:20]}"
            
            embed = discord.Embed(
                title="🟢 Red Legion Bot Health Status", 
                description="Bot is running normally",
                color=discord.Color.green()
            )
            embed.add_field(name="Uptime", value=str(uptime), inline=True)
            embed.add_field(name="Guilds", value=guild_count, inline=True)
            embed.add_field(name="Memory", value=memory_str, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"⚠️ Health check error: {str(e)}")

    @app_commands.command(name="redtest", description="Comprehensive Red Legion bot health and system status")
    async def test_command(self, interaction: discord.Interaction):
        """🔧 Bot Test & Health Status - Comprehensive bot health and system status"""
        try:
            # Calculate uptime
            if hasattr(self.bot, 'start_time'):
                uptime = datetime.now() - self.bot.start_time
                uptime_str = str(uptime).split('.')[0]  # Remove microseconds
            else:
                uptime_str = "Unknown"
            
            # Get Discord connection info
            guild_count = len(self.bot.guilds)
            total_members = sum(guild.member_count for guild in self.bot.guilds if guild.member_count)
            latency_ms = round(self.bot.latency * 1000, 2)
            
            # Get system info with enhanced error handling
            memory_info = "N/A"
            cpu_info = "N/A"
            process_status = "Unknown"
            try:
                import psutil
                process = psutil.Process(os.getpid())
                memory_mb = process.memory_info().rss / 1024 / 1024
                cpu_percent = process.cpu_percent()
                memory_info = f"{memory_mb:.1f} MB"
                cpu_info = f"{cpu_percent:.1f}%"
                process_status = "Running"
            except ImportError:
                memory_info = "psutil not available"
                cpu_info = "psutil not available"
                process_status = "Running (psutil unavailable)"
            except Exception as e:
                memory_info = f"Error: {str(e)[:20]}"
                cpu_info = f"Error: {str(e)[:20]}"
                process_status = "Error getting status"
            
            # Test database connection with detailed status
            db_status = "❌ Not tested"
            try:
                from config.settings import get_database_url
                db_url = get_database_url()
                
                if db_url:
                    try:
                        import psycopg2
                        from urllib.parse import urlparse
                        
                        # Test connection
                        parsed = urlparse(db_url)
                        if parsed.hostname not in ['127.0.0.1', 'localhost']:
                            # Try proxy first, then direct
                            proxy_url = db_url.replace(f'{parsed.hostname}:{parsed.port}', '127.0.0.1:5433')
                            try:
                                test_conn = psycopg2.connect(proxy_url)
                                test_conn.close()
                                db_status = "✅ Connected (via proxy)"
                            except:
                                test_conn = psycopg2.connect(db_url)
                                test_conn.close()
                                db_status = "✅ Connected (direct)"
                        else:
                            test_conn = psycopg2.connect(db_url)
                            test_conn.close()
                            db_status = "✅ Connected (local)"
                    except Exception as db_e:
                        db_status = f"❌ Failed: {str(db_e)[:30]}"
                else:
                    db_status = "❌ No URL configured"
            except ImportError:
                db_status = "❌ psycopg2 not available"
            except Exception as e:
                db_status = f"❌ Error: {str(e)[:30]}"
            
            # Get Discord-specific info
            voice_info = "N/A"
            if interaction.guild:
                voice_channels_count = len(interaction.guild.voice_channels)
                voice_info = f"{voice_channels_count} voice channels"
            
            # Permission check
            permission_info = "Standard User"
            if interaction.user.guild_permissions.administrator:
                permission_info = "Administrator"
            elif interaction.user.guild_permissions.manage_guild:
                permission_info = "Manager"
            
            # Create comprehensive status embed
            embed = discord.Embed(
                title="🔧 Red Legion Bot Comprehensive Test",
                description="Complete system health and connectivity report",
                color=discord.Color.blue()
            )
            
            # Core Status
            embed.add_field(
                name="🤖 Bot Status",
                value=f"**Status:** {process_status}\n"
                      f"**Uptime:** {uptime_str}\n"
                      f"**Latency:** {latency_ms}ms",
                inline=True
            )
            
            # System Resources
            embed.add_field(
                name="💻 System Resources",
                value=f"**Memory:** {memory_info}\n"
                      f"**CPU:** {cpu_info}\n"
                      f"**Process:** Active",
                inline=True
            )
            
            # Discord Integration
            embed.add_field(
                name="🌐 Discord Integration",
                value=f"**Guilds:** {guild_count}\n"
                      f"**Members:** {total_members}\n"
                      f"**Voice:** {voice_info}",
                inline=True
            )
            
            # Database Status
            embed.add_field(
                name="🗃️ Database",
                value=f"**Status:** {db_status}",
                inline=True
            )
            
            # User Info
            embed.add_field(
                name="👤 User Info",
                value=f"**Permissions:** {permission_info}\n"
                      f"**User:** {interaction.user.display_name}",
                inline=True
            )
            
            # Add timestamp
            embed.set_footer(
                text=f"Test run by {interaction.user.display_name} • Response time: {latency_ms}ms"
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            # Error fallback embed
            error_embed = discord.Embed(
                title="⚠️ Test Error",
                description="Bot is responding but test encountered an error",
                color=discord.Color.orange()
            )
            error_embed.add_field(name="Error", value=f"`{str(e)[:100]}`", inline=False)
            error_embed.add_field(name="Basic Info", value=f"Guilds: {len(self.bot.guilds)}\\nLatency: {round(self.bot.latency * 1000, 2)}ms", inline=False)
            
            await interaction.response.send_message(embed=error_embed)

    @app_commands.command(name="reddbtest", description="Test Red Legion bot database connectivity (Admin only)")
    @app_commands.default_permissions(administrator=True)
    async def dbtest_command(self, interaction: discord.Interaction):
        """Test database connectivity and performance"""
        try:
            from config.settings import get_database_url
            db_url = get_database_url()
            
            if not db_url:
                await interaction.response.send_message("❌ No database URL configured")
                return
            
            # Test basic connection
            start_time = datetime.now()
            try:
                import psycopg2
                from urllib.parse import urlparse
                
                # Parse and test connection
                parsed = urlparse(db_url)
                connection_method = "unknown"
                
                if parsed.hostname not in ['127.0.0.1', 'localhost']:
                    # Try proxy first, then direct
                    proxy_url = db_url.replace(f'{parsed.hostname}:{parsed.port}', '127.0.0.1:5433')
                    try:
                        conn = psycopg2.connect(proxy_url)
                        connection_method = "Cloud SQL Proxy"
                    except:
                        conn = psycopg2.connect(db_url)
                        connection_method = "Direct Connection"
                else:
                    conn = psycopg2.connect(db_url)
                    connection_method = "Local Database"
                
                # Test basic query
                cursor = conn.cursor()
                cursor.execute("SELECT version(), current_database(), current_user;")
                db_info = cursor.fetchone()
                
                # Test tables
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name;
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                conn.close()
                connection_time = (datetime.now() - start_time).total_seconds() * 1000
                
                embed = discord.Embed(
                    title="✅ Red Legion Database Test Results",
                    description="Database connectivity test completed successfully",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="🔗 Connection",
                    value=f"**Method:** {connection_method}\\n"
                          f"**Time:** {connection_time:.2f}ms\\n"
                          f"**Status:** Connected",
                    inline=True
                )
                
                embed.add_field(
                    name="🗃️ Database Info",
                    value=f"**Database:** {db_info[1]}\\n"
                          f"**User:** {db_info[2]}\\n"
                          f"**Tables:** {len(tables)}",
                    inline=True
                )
                
                # List important tables
                important_tables = ['mining_events', 'mining_participation', 'events', 'users', 'guilds']
                found_tables = [t for t in important_tables if t in tables]
                missing_tables = [t for t in important_tables if t not in tables]
                
                tables_status = ""
                if found_tables:
                    tables_status += f"**Found:** {', '.join(found_tables)}\\n"
                if missing_tables:
                    tables_status += f"**Missing:** {', '.join(missing_tables)}"
                
                embed.add_field(
                    name="📋 Schema Status",
                    value=tables_status or "All important tables found",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed)
                
            except Exception as db_error:
                embed = discord.Embed(
                    title="❌ Red Legion Database Test Failed",
                    description="Could not connect to or query the database",
                    color=discord.Color.red()
                )
                embed.add_field(name="Error", value=f"`{str(db_error)[:200]}`", inline=False)
                await interaction.response.send_message(embed=embed)
                
        except Exception as e:
            await interaction.response.send_message(f"❌ Database test error: {str(e)}")

    @app_commands.command(name="redconfig", description="Check Red Legion bot configuration status (Admin only)")
    @app_commands.default_permissions(administrator=True)
    async def config_check(self, interaction: discord.Interaction):
        """Check configuration status and settings"""
        try:
            from config.settings import DISCORD_CONFIG, get_database_url
            
            embed = discord.Embed(
                title="⚙️ Red Legion Bot Configuration",
                description="Current configuration status",
                color=discord.Color.blue()
            )
            
            # Discord Config
            token_status = "✅ Present" if DISCORD_CONFIG.get('TOKEN') else "❌ Missing"
            embed.add_field(
                name="🤖 Discord Settings",
                value=f"**Token:** {token_status}\\n"
                      f"**Guilds:** {len(self.bot.guilds)}",
                inline=True
            )
            
            # Database Config
            db_url = get_database_url()
            db_status = "✅ Configured" if db_url else "❌ Missing"
            embed.add_field(
                name="🗃️ Database Settings",
                value=f"**URL:** {db_status}",
                inline=True
            )
            
            # Environment Info
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            embed.add_field(
                name="🐍 Environment",
                value=f"**Python:** {python_version}\\n"
                      f"**Platform:** {sys.platform}",
                inline=True
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Config check error: {str(e)}")


async def setup(bot):
    """Setup function for discord.py extension loading."""
    await bot.add_cog(Diagnostics(bot))
    print("✅ Diagnostics commands loaded")
