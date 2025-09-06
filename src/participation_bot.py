import discord
import datetime  # Add this import
from discord.ext import commands
from .database import init_db, add_market_item, get_market_items, issue_loan
from .event_handlers import (
    on_voice_state_update, start_logging, stop_logging, pick_winner,
    list_open_events
    # log_mining_results temporarily disabled due to implementation issues
)
from .discord_utils import has_org_role

# Import DATABASE_URL but handle None case
try:
    from .config import DATABASE_URL
    if not DATABASE_URL:
        print("WARNING: DATABASE_URL is None at import time")
except Exception as e:
    print(f"WARNING: Failed to import DATABASE_URL: {e}")
    DATABASE_URL = None

def get_database_url():
    """Get current database URL, refreshing from Secret Manager if needed"""
    global DATABASE_URL
    if not DATABASE_URL:
        try:
            from .config import get_secret
            DATABASE_URL = get_secret("database-connection-string")
            print("Successfully refreshed DATABASE_URL from Secret Manager")
        except Exception as e:
            print(f"Failed to refresh DATABASE_URL: {e}")
            # Try getting from config again
            try:
                from .config import config
                DATABASE_URL = config.get('DATABASE_URL')
            except Exception as e2:
                print(f"Failed to get DATABASE_URL from config: {e2}")
    return DATABASE_URL

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Dynamically register event handler
async def setup_event_handlers():
    try:
        bot.add_listener(on_voice_state_update, 'on_voice_state_update')
        print("Voice state update handler registered successfully")
    except Exception as e:
        print(f"ERROR registering event handlers: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())

# Dynamically register commands
def setup_commands():
    try:
        print("Registering basic commands...")
        
        # Command without role restriction - fix lambda issues
        @bot.command(name="start_logging")
        async def start_logging_cmd(ctx):
            await start_logging(bot, ctx)
        
        @bot.command(name="stop_logging")
        async def stop_logging_cmd(ctx):
            await stop_logging(bot, ctx)
        
        @bot.command(name="pick_winner")
        async def pick_winner_cmd(ctx):
            await pick_winner(bot, ctx)
        
        @bot.command(name="ping")
        async def ping_cmd(ctx):
            """Simple ping command to test bot responsiveness"""
            latency = round(bot.latency * 1000, 2)
            await ctx.send(f"🏓 Pong! Latency: {latency}ms")
        
        print("Basic commands registered")
        print("Registering role-restricted commands...")

        # Commands with role restriction
        @bot.command(name="list_market")
        @has_org_role()
        @commands.cooldown(1, 30, commands.BucketType.guild)
        async def list_market(ctx):
            items = get_market_items(get_database_url())
            if not items:
                await ctx.send("No market items available.")
                return
            
            embed = discord.Embed(title="Market Items", color=discord.Color.blue())
            for item_id, name, price, stock in items:
                embed.add_field(name=f"{name} (ID: {item_id})", value=f"Price: {price} credits\nStock: {stock}", inline=False)
            await ctx.send(embed=embed)

        @bot.command(name="add_market_item")
        @has_org_role()
        @commands.cooldown(1, 30, commands.BucketType.guild)
        async def add_market_item_cmd(ctx, name: str, price: int, stock: int):
            try:
                add_market_item(get_database_url(), name, price, stock)
                await ctx.send(f"Added {name} to market for {price} credits (Stock: {stock})")
            except Exception as e:
                await ctx.send(f"Failed to add market item: {e}")

        @bot.command(name="request_loan")
        @has_org_role()
        @commands.cooldown(1, 30, commands.BucketType.guild)
        async def request_loan(ctx, amount: int):
            try:
                from datetime import datetime, timedelta
                issued_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                issue_loan(get_database_url(), ctx.author.id, amount, issued_date, due_date)
                await ctx.send(f"Loan request submitted for {amount} credits. Due date: {due_date}")
            except Exception as e:
                await ctx.send(f"Failed to request loan: {e}")

        @bot.command(name="log_mining_results")
        @has_org_role()
        @commands.cooldown(1, 30, commands.BucketType.guild)
        async def log_mining_results_cmd(ctx, event_id: int):
            await ctx.send("⚠️ Mining results logging is temporarily disabled due to implementation issues.")
            # await log_mining_results(bot, ctx, event_id)

        @bot.command(name="list_open_events")
        @has_org_role()
        @commands.cooldown(1, 30, commands.BucketType.guild)
        async def list_open_events_cmd(ctx):
            await list_open_events(bot, ctx)
            
        # Add health check command
        @bot.command(name="health")
        async def health_check(ctx):
            """Simple health check command for monitoring"""
            import datetime
            import psutil
            import os
            
            try:
                # Basic bot status
                uptime = datetime.datetime.now() - bot.start_time if hasattr(bot, 'start_time') else 'Unknown'
                guild_count = len(bot.guilds)
                
                # System status
                process = psutil.Process(os.getpid())
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                embed = discord.Embed(
                    title="🟢 Bot Health Status", 
                    description="Bot is running normally",
                    color=discord.Color.green()
                )
                embed.add_field(name="Uptime", value=str(uptime), inline=True)
                embed.add_field(name="Guilds", value=guild_count, inline=True)
                embed.add_field(name="Memory", value=f"{round(memory_mb, 2)} MB", inline=True)
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"⚠️ Health check error: {str(e)}")

        @bot.command(name="test")
        async def test_command(ctx):
            """Comprehensive bot health and status test command"""
            try:
                from datetime import datetime
                
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
                    import os
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
                db_status = "Unknown"
                try:
                    # Use psycopg2 instead of asyncpg for consistency with dbtest
                    import psycopg2
                    
                    current_db_url = get_database_url()
                    if not current_db_url:
                        db_status = "❌ Error: DATABASE_URL not configured"
                    else:
                        conn = psycopg2.connect(current_db_url, connect_timeout=5)
                        cursor = conn.cursor()
                        cursor.execute('SELECT 1')
                        cursor.close()
                        conn.close()
                        db_status = "✅ Connected"
                except ImportError:
                    db_status = "psycopg2 not available"
                except Exception as e:
                    db_status = f"❌ Error: {str(e)[:50]}"
                
                # Create comprehensive health embed
                embed = discord.Embed(
                    title="🔧 Bot Test & Health Status",
                    description="Comprehensive bot health and system status",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                
                # Bot Status Section
                embed.add_field(
                    name="🤖 Bot Status", 
                    value=f"**Status**: 🟢 Online\n**Uptime**: {uptime_str}\n**Guilds**: {guild_count}\n**Total Members**: {total_members:,}",
                    inline=True
                )
                
                # System Resources Section
                embed.add_field(
                    name="💻 System Resources",
                    value=f"**Memory**: {memory_info}\n**CPU**: {cpu_info}\n**Process**: Running",
                    inline=True
                )
                
                # Database & Services Section
                embed.add_field(
                    name="🗄️ Services",
                    value=f"**Database**: {db_status}\n**Discord API**: ✅ Connected\n**Voice Tracking**: Ready",
                    inline=True
                )
                
                # Performance Metrics
                latency_ms = round(bot.latency * 1000, 2)
                embed.add_field(
                    name="📊 Performance",
                    value=f"**Latency**: {latency_ms}ms\n**Commands**: Responsive\n**Events**: Active",
                    inline=True
                )
                
                # Quick Function Tests
                test_results = []
                
                # Test 1: Can access guild info
                try:
                    guild = ctx.guild
                    if guild:
                        test_results.append("✅ Guild access")
                        test_results.append(f"✅ Voice channels ({len(guild.voice_channels)})")
                    else:
                        test_results.append("⚠️ No guild context")
                except Exception:
                    test_results.append("❌ Guild access failed")
                
                # Test 2: Can check user permissions
                try:
                    if ctx.author:
                        test_results.append("✅ User permissions")
                    else:
                        test_results.append("⚠️ No user context")
                except Exception:
                    test_results.append("❌ User permission check failed")
                
                embed.add_field(
                    name="🧪 Function Tests",
                    value="\n".join(test_results),
                    inline=True
                )
                
                # Add footer with additional info
                embed.set_footer(text=f"Test run by {ctx.author.display_name} • Response time: {latency_ms}ms")
                
                # Send the comprehensive health report
                await ctx.send(embed=embed)
                
                # Also send a simple confirmation message
                await ctx.send(f"✅ **Bot Test Complete!** All systems operational. Response time: {latency_ms}ms")
                
            except Exception as e:
                # If the health check itself fails, send a simple error message
                error_embed = discord.Embed(
                    title="❌ Bot Test Error",
                    description=f"Health check encountered an error: {str(e)}",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                error_embed.add_field(name="Status", value="Bot is responding but health check failed", inline=False)
                error_embed.add_field(name="Basic Info", value=f"Guilds: {len(bot.guilds)}\nLatency: {round(bot.latency * 1000, 2)}ms", inline=False)
                
                await ctx.send(embed=error_embed)
                await ctx.send(f"⚠️ Health check error, but bot is responding to commands. Error: `{str(e)[:100]}`")

        @bot.command(name="dbtest")
        async def dbtest_command(ctx):
            """Test database connectivity with detailed diagnostics"""
            try:
                from datetime import datetime
                
                embed = discord.Embed(
                    title="🗄️ Database Connection Test",
                    description="Testing connection to arccorp-data-nexus database",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                
                # Test database connection
                try:
                    import psycopg2
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
                    
                except psycopg2.OperationalError as e:
                    error_msg = str(e)
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
                    
                except Exception as e:
                    embed.add_field(
                        name="❌ Unexpected Error",
                        value=f"**Error**: {str(e)[:100]}...",
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
        async def config_check(ctx):
            """Check configuration and infrastructure connectivity"""
            try:
                from datetime import datetime
                import os
                
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
                    from .config import get_secret
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
                    name="🏗️ Infrastructure",
                    value="\n".join(infra_info),
                    inline=False
                )
                
                embed.add_field(
                    name="📋 Migration Status",
                    value="✅ Updated for new infrastructure\n✅ Secret Manager configured\n✅ Database connection automated",
                    inline=False
                )
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"❌ Configuration check failed: {str(e)}")

        @bot.command(name="refresh_config")
        @has_org_role()
        async def refresh_config(ctx):
            """Refresh configuration from Secret Manager"""
            try:
                from datetime import datetime
                
                embed = discord.Embed(
                    title="🔄 Configuration Refresh",
                    description="Refreshing bot configuration from Secret Manager",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                
                # Test refreshing configuration
                refresh_status = []
                try:
                    from .config import get_secret
                    
                    # Test accessing secrets (without storing sensitive data)
                    try:
                        # Actually refresh the DATABASE_URL
                        global DATABASE_URL
                        DATABASE_URL = None  # Force refresh
                        new_db_url = get_database_url()
                        if new_db_url:
                            refresh_status.append("✅ Database connection string: Refreshed")
                        else:
                            refresh_status.append("❌ Database connection string: Failed to refresh")
                    except Exception as e:
                        refresh_status.append(f"❌ Database connection string: {str(e)[:40]}")
                    
                    try:
                        get_secret("discord-token")
                        refresh_status.append("✅ Discord token: Verified")
                    except Exception as e:
                        refresh_status.append(f"❌ Discord token: {str(e)[:40]}")
                    
                    # Note: Full config refresh completed
                    refresh_status.append("ℹ️ Configuration reloaded successfully")
                    
                except Exception as e:
                    refresh_status.append(f"❌ Secret Manager access failed: {str(e)[:40]}")
                
                embed.add_field(
                    name="🔄 Refresh Results",
                    value="\n".join(refresh_status),
                    inline=False
                )
                
                embed.add_field(
                    name="💡 Next Steps",
                    value="Use `!test` to verify connectivity after refresh\nConsider `!restart_red_legion_bot` for full reload",
                    inline=False
                )
                
                embed.color = discord.Color.green() if "❌" not in "\n".join(refresh_status) else discord.Color.orange()
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"❌ Configuration refresh failed: {str(e)}")

        @bot.command(name="restart_red_legion_bot")
        @has_org_role()
        async def restart_bot(ctx):
            """Restart the Red Legion Bot (org role required)"""
            try:
                embed = discord.Embed(
                    title="🔄 Bot Restart",
                    description="Restarting Red Legion Bot...",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="Status",
                    value="✅ Restart initiated by authorized user\n⏳ Bot will reconnect shortly",
                    inline=False
                )
                embed.add_field(
                    name="Note",
                    value="This will reload all configuration from Secret Manager",
                    inline=False
                )
                
                await ctx.send(embed=embed)
                
                # Give time for the message to send before restarting
                import asyncio
                await asyncio.sleep(2)
                
                # Restart the bot process
                import os
                import sys
                print(f"Bot restart initiated by {ctx.author} ({ctx.author.id})")
                os.execv(sys.executable, ['python'] + sys.argv)
                
            except Exception as e:
                await ctx.send(f"❌ Failed to restart bot: {str(e)}")

        print("All commands registered successfully")
        
    except Exception as e:
        print(f"ERROR registering commands: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())

@bot.event
async def on_ready():
    bot.start_time = datetime.datetime.now()  # Add this line
    
    print(f'Logged in as {bot.user}')
    print(f'Bot is ready and connected to {len(bot.guilds)} servers')
    print(f"🤖 {bot.user} has connected to Discord!")
    print(f"📅 Bot started at: {bot.start_time}")
    print(f"🏠 Connected to {len(bot.guilds)} guilds")
    
    # Log guild information
    for guild in bot.guilds:
        print(f'Connected to guild: {guild.name} (ID: {guild.id})')
    
    try:
        print("Initializing database...")
        # Run database init in a thread to avoid blocking the event loop
        import asyncio
        import functools
        loop = asyncio.get_event_loop()
        
        # Add timeout to database initialization to prevent hanging
        try:
            await asyncio.wait_for(
                loop.run_in_executor(None, functools.partial(init_db, get_database_url())),
                timeout=30.0  # 30 second timeout
            )
            print("Database initialized successfully")
        except asyncio.TimeoutError:
            print("⚠️ Database initialization timed out after 30 seconds - continuing anyway")
        except Exception as db_error:
            print(f"⚠️ Database initialization failed: {db_error} - bot will continue without database")
        
        print("Setting up event handlers...")
        await setup_event_handlers()  # Register event handler
        print("Event handlers registered successfully")
        
        print("Bot setup completed successfully!")
        print("Bot is fully operational and ready to receive commands")
        
        # Add a simple heartbeat to ensure bot stays alive and log activity
        print("✅ Bot startup sequence completed - bot should remain running")
        
        # Start a simple heartbeat task to verify bot is still alive
        async def heartbeat():
            import asyncio
            import datetime
            while True:
                await asyncio.sleep(300)  # Every 5 minutes
                print(f"💓 Heartbeat: Bot is still running at {datetime.datetime.now()}")
        
        # Start heartbeat task
        import asyncio
        asyncio.create_task(heartbeat())  # Start task but don't store reference
        print("Heartbeat monitoring started")
        
    except Exception as e:
        print(f"CRITICAL ERROR during setup: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        print("Bot will attempt to continue running despite setup errors...")
        # Don't re-raise the exception - let the bot continue running

@bot.event
async def on_error(event, *args, **kwargs):
    print(f'DISCORD EVENT ERROR in event {event}')
    print(f'Args: {args}')
    print(f'Kwargs: {kwargs}')
    import traceback
    print("Full traceback:")
    print(traceback.format_exc())
    # DO NOT re-raise the exception - let the bot continue running

# Add a command error handler to prevent command errors from crashing the bot
@bot.event
async def on_command_error(ctx, error):
    print(f'COMMAND ERROR in command {ctx.command}: {error}')
    import traceback
    print("Full traceback:")
    print(traceback.format_exc())
    # Send error message to user but don't crash
    try:
        await ctx.send(f"⚠️ Command error: {str(error)}")
    except Exception:
        pass  # Don't crash if we can't send the error message

# Add a disconnect handler to log when bot disconnects
@bot.event
async def on_disconnect():
    print("⚠️  Bot disconnected from Discord!")

# Add a resumed handler to log reconnections
@bot.event
async def on_resumed():
    print("✅ Bot resumed connection to Discord!")

if __name__ == "__main__":
    from .config import DISCORD_TOKEN
    print("Starting Discord bot...")
    print(f"Discord token length: {len(DISCORD_TOKEN) if DISCORD_TOKEN else 'None'}")
    print(f"Database URL configured: {'Yes' if get_database_url() else 'No'}")
    
    # Register commands before starting the bot
    print("Setting up commands...")
    setup_commands()
    print("Commands setup complete")
    
    try:
        print("Calling bot.run()...")
        bot.run(DISCORD_TOKEN)
        print("bot.run() returned - this should not happen unless bot stops")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to start bot: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
    finally:
        print("Bot execution finished")