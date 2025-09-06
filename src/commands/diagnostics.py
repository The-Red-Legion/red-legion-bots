"""
Diagnostic and health check commands for the Red Legion Discord bot.

This module contains commands for monitoring bot health, testing connectivity,
and checking configuration status.
"""

import discord
from discord.ext import commands
from datetime import datetime
import os
from ..core.decorators import has_org_role, standard_cooldown, error_handler


def register_commands(bot):
    """Register all diagnostic commands with the bot."""
    
    @bot.command(name="health")
    @error_handler
    async def health_check(ctx):
        """Simple health check command for monitoring"""
        try:
            # Basic bot status
            uptime = datetime.now() - bot.start_time if hasattr(bot, 'start_time') else 'Unknown'
            guild_count = len(bot.guilds)
            
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
                title="🟢 Bot Health Status", 
                description="Bot is running normally",
                color=discord.Color.green()
            )
            embed.add_field(name="Uptime", value=str(uptime), inline=True)
            embed.add_field(name="Guilds", value=guild_count, inline=True)
            embed.add_field(name="Memory", value=memory_str, inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"⚠️ Health check error: {str(e)}")

    @bot.command(name="test")
    @error_handler
    async def test_command(ctx):
        """Comprehensive bot health and status test command"""
        try:
            # Calculate uptime
            if hasattr(bot, 'start_time'):
                uptime = datetime.now() - bot.start_time
                uptime_str = str(uptime).split('.')[0]  # Remove microseconds
            else:
                uptime_str = "Unknown"
            
            # Get Discord connection info
            guild_count = len(bot.guilds)
            total_members = sum(guild.member_count for guild in bot.guilds if guild.member_count)
            
            # Try to get system info if psutil is available
            memory_info = "N/A"
            cpu_info = "N/A"
            try:
                import psutil
                process = psutil.Process(os.getpid())
                memory_mb = process.memory_info().rss / 1024 / 1024
                cpu_percent = process.cpu_percent()
                memory_info = f"{memory_mb:.1f} MB"
                cpu_info = f"{cpu_percent:.1f}%"
            except ImportError:
                memory_info = "psutil not available"
                cpu_info = "psutil not available"
            except Exception as e:
                memory_info = f"Error: {str(e)[:20]}"
                cpu_info = f"Error: {str(e)[:20]}"
            
            # Test database connection
            db_status = "❌ Not tested"
            try:
                from ..config import get_database_url
                
                # Try to get database URL from config
                db_url = get_database_url()
                
                if not db_url:
                    db_status = "❌ DATABASE_URL not configured"
                else:
                    import psycopg2
                    conn = psycopg2.connect(db_url, connect_timeout=5)
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1;")
                    cursor.fetchone()
                    db_status = "✅ Connected"
                    conn.close()
            except Exception as e:
                db_status = f"❌ Error: {str(e)[:30]}"
            
            # Create comprehensive embed
            embed = discord.Embed(
                title="🔍 Comprehensive Bot Test",
                description="Complete system status check",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            # Bot info
            embed.add_field(
                name="🤖 Bot Status",
                value=f"**Uptime**: {uptime_str}\n**Latency**: {round(bot.latency * 1000, 2)}ms\n**Guilds**: {guild_count}\n**Total Members**: {total_members}",
                inline=False
            )
            
            # System info
            embed.add_field(
                name="💻 System Resources",
                value=f"**Memory**: {memory_info}\n**CPU**: {cpu_info}",
                inline=True
            )
            
            # Database status
            embed.add_field(
                name="🗄️ Database",
                value=db_status,
                inline=True
            )
            
            # Infrastructure info
            embed.add_field(
                name="🏗️ Infrastructure",
                value="**Instance**: arccorp-compute\n**Database**: arccorp-data-nexus\n**Project**: rl-prod-471116",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            # Create error embed if main test fails
            error_embed = discord.Embed(
                title="⚠️ Test Error",
                description=f"Health check encountered an error: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            error_embed.add_field(name="Status", value="Bot is responding but health check failed", inline=False)
            error_embed.add_field(name="Basic Info", value=f"Guilds: {len(bot.guilds)}\nLatency: {round(bot.latency * 1000, 2)}ms", inline=False)
            
            await ctx.send(embed=error_embed)
            await ctx.send(f"⚠️ Health check error, but bot is responding to commands. Error: `{str(e)[:100]}`")

    @bot.command(name="dbtest")
    @error_handler
    async def dbtest_command(ctx):
        """Test database connectivity with detailed diagnostics"""
        try:
            embed = discord.Embed(
                title="🗄️ Database Connection Test",
                description="Testing connection to arccorp-data-nexus database",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            # Test database connection
            try:
                import psycopg2
                from ..config import get_database_url
                
                current_db_url = get_database_url()
                if not current_db_url:
                    embed.add_field(
                        name="❌ Configuration Error",
                        value="DATABASE_URL is not configured",
                        inline=False
                    )
                    embed.add_field(
                        name="💡 Suggestion",
                        value="Check Secret Manager configuration or environment variables",
                        inline=False
                    )
                    embed.color = discord.Color.red()
                else:
                    conn = psycopg2.connect(current_db_url, connect_timeout=10)
                    cursor = conn.cursor()
                    cursor.execute("SELECT version();")
                    version_info = cursor.fetchone()[0]
                    cursor.execute("SELECT current_database();")
                    db_name = cursor.fetchone()[0]
                    cursor.execute("SELECT current_user;")
                    db_user = cursor.fetchone()[0]
                    
                    embed.add_field(
                        name="✅ Connection Status",
                        value="Successfully connected to database",
                        inline=False
                    )
                    embed.add_field(
                        name="📋 Database Info",
                        value=f"**Database**: {db_name}\n**User**: {db_user}\n**Version**: {version_info[:50]}...",
                        inline=False
                    )
                    embed.color = discord.Color.green()
                    conn.close()
                
            except Exception as db_error:
                if "psycopg2" in str(type(db_error)):
                    error_msg = str(db_error)
                    embed.add_field(
                        name="❌ Connection Failed",
                        value=f"**Error**: {error_msg[:100]}...",
                        inline=False
                    )
                    
                    # Add troubleshooting suggestions
                    if "authentication failed" in error_msg.lower():
                        embed.add_field(
                            name="💡 Suggestion",
                            value="Database credentials may have changed. Try `!refresh_config`",
                            inline=False
                        )
                    elif "timeout" in error_msg.lower() or "could not connect" in error_msg.lower():
                        embed.add_field(
                            name="💡 Suggestion", 
                            value="Database server may be unreachable. Check arccorp-data-nexus status.",
                            inline=False
                        )
                    elif "does not exist" in error_msg.lower():
                        embed.add_field(
                            name="💡 Suggestion",
                            value="Database configuration issue. Verify database name and host.",
                            inline=False
                        )
                    embed.color = discord.Color.red()
                else:
                    embed.add_field(
                        name="❌ Unexpected Error",
                        value=f"**Error**: {str(db_error)[:100]}...",
                        inline=False
                    )
                    embed.add_field(
                        name="💡 Suggestion",
                        value="Check bot logs for detailed error information.",
                        inline=False
                    )
                    embed.color = discord.Color.red()
            
            # Add infrastructure info
            embed.add_field(
                name="🏗️ Infrastructure",
                value="**Instance**: arccorp-compute\n**Database**: arccorp-data-nexus\n**Connection**: Via Secret Manager",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Database test failed: {str(e)}")

    @bot.command(name="config_check")
    @has_org_role()
    @error_handler
    async def config_check(ctx):
        """Check configuration and infrastructure connectivity"""
        try:
            embed = discord.Embed(
                title="🔧 Configuration Check",
                description="Infrastructure and configuration status",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            # Check environment variables
            env_status = []
            env_vars = ['GOOGLE_CLOUD_PROJECT', 'TEXT_CHANNEL_ID', 'ORG_ROLE_ID']
            for var in env_vars:
                value = os.getenv(var)
                if value:
                    env_status.append(f"✅ {var}: Set")
                else:
                    env_status.append(f"⚠️ {var}: Not set")
            
            embed.add_field(
                name="🌍 Environment Variables",
                value="\n".join(env_status),
                inline=False
            )
            
            # Check Secret Manager access
            secret_status = []
            try:
                from ..config import get_secret
                # Test if we can access Secret Manager (without exposing values)
                try:
                    get_secret("database-connection-string")
                    secret_status.append("✅ Database connection string: Accessible")
                except Exception as e:
                    secret_status.append(f"❌ Database connection string: {str(e)[:30]}")
                
                try:
                    get_secret("discord-token")
                    secret_status.append("✅ Discord token: Accessible")
                except Exception as e:
                    secret_status.append(f"❌ Discord token: {str(e)[:30]}")
                    
            except Exception as e:
                secret_status.append(f"❌ Secret Manager: {str(e)[:40]}")
            
            embed.add_field(
                name="🔐 Secret Manager",
                value="\n".join(secret_status),
                inline=False
            )
            
            # Quick database connectivity test
            db_test = "❌ Not tested"
            try:
                import psycopg2
                from ..config import get_database_url
                
                db_url = get_database_url()
                if not db_url:
                    db_test = "❌ Error: DATABASE_URL not configured"
                else:
                    conn = psycopg2.connect(db_url, connect_timeout=5)
                    cursor = conn.cursor()
                    cursor.execute("SELECT version();")
                    cursor.fetchone()[0]  # Just test the connection, don't store
                    db_test = "✅ Connected (PostgreSQL)"
                    conn.close()
            except Exception as e:
                db_test = f"❌ Error: {str(e)[:40]}"
            
            embed.add_field(
                name="🗄️ Database Connection",
                value=db_test,
                inline=False
            )
            
            # Infrastructure info (if available)
            infra_info = []
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'rl-prod-471116')
            infra_info.append(f"📍 Project: {project_id}")
            infra_info.append("🏗️ Instance: arccorp-compute")
            infra_info.append("🗄️ Database: arccorp-data-nexus")
            
            embed.add_field(
                name="🏗️ Infrastructure Info",
                value="\n".join(infra_info),
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Configuration check failed: {str(e)}")

    print("✅ Diagnostic commands registered")
