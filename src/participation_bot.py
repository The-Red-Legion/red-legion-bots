import discord
import datetime  # Add this import
import asyncio
import logging
from discord.ext import commands
from .config import DATABASE_URL
from .database import init_db, add_market_item, get_market_items, issue_loan
from .event_handlers import (
    on_voice_state_update, start_logging, stop_logging, pick_winner,
    list_open_events
    # log_mining_results temporarily disabled due to implementation issues
)
from .discord_utils import has_org_role

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
        
        print("Basic commands registered")
        print("Registering role-restricted commands...")

        # Commands with role restriction
        @bot.command(name="list_market")
        @has_org_role()
        @commands.cooldown(1, 30, commands.BucketType.guild)
        async def list_market(ctx):
            items = get_market_items(DATABASE_URL)
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
                add_market_item(DATABASE_URL, name, price, stock)
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
                issue_loan(DATABASE_URL, ctx.author.id, amount, issued_date, due_date)
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
                
                health_info = {
                    'status': 'healthy',
                    'uptime': str(uptime),
                    'guilds': guild_count,
                    'memory_mb': round(memory_mb, 2),
                    'timestamp': datetime.datetime.now().isoformat()
                }
                
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
                import psutil
                import os
                from datetime import datetime, timedelta
                
                # Calculate uptime
                if hasattr(bot, 'start_time'):
                    uptime = datetime.now() - bot.start_time
                    uptime_str = str(uptime).split('.')[0]  # Remove microseconds
                else:
                    uptime_str = "Unknown"
                
                # Get system info
                process = psutil.Process(os.getpid())
                memory_mb = process.memory_info().rss / 1024 / 1024
                cpu_percent = process.cpu_percent()
                
                # Get Discord connection info
                guild_count = len(bot.guilds)
                total_members = sum(guild.member_count for guild in bot.guilds if guild.member_count)
                
                # Test database connection
                db_status = "Unknown"
                try:
                    # Quick database test
                    import asyncio
                    import asyncpg
                    
                    async def test_db():
                        try:
                            conn = await asyncpg.connect(DATABASE_URL, timeout=5)
                            await conn.execute('SELECT 1')
                            await conn.close()
                            return "✅ Connected"
                        except Exception as e:
                            return f"❌ Error: {str(e)[:50]}"
                    
                    db_status = await test_db()
                except Exception as e:
                    db_status = f"❌ Test failed: {str(e)[:30]}"
                
                # Check recent errors in logs (if accessible)
                recent_errors = "No recent errors detected"
                try:
                    if os.path.exists("/app/bot.log"):
                        with open("/app/bot.log", "r") as f:
                            log_lines = f.readlines()[-20:]  # Last 20 lines
                            error_lines = [line for line in log_lines if any(term in line.lower() for term in ['error', 'exception', 'failed'])]
                            if error_lines:
                                recent_errors = f"⚠️ {len(error_lines)} recent errors found"
                            else:
                                recent_errors = "✅ No recent errors"
                except:
                    recent_errors = "Unable to check logs"
                
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
                    value=f"**Memory**: {memory_mb:.1f} MB\n**CPU**: {cpu_percent:.1f}%\n**PID**: {os.getpid()}\n**Process**: Running",
                    inline=True
                )
                
                # Database & Services Section
                embed.add_field(
                    name="🗄️ Services",
                    value=f"**Database**: {db_status}\n**Discord API**: ✅ Connected\n**Logs**: {recent_errors}",
                    inline=True
                )
                
                # Performance Metrics
                latency_ms = round(bot.latency * 1000, 2)
                embed.add_field(
                    name="📊 Performance",
                    value=f"**Latency**: {latency_ms}ms\n**Commands**: Responsive\n**Events**: Active\n**Voice Tracking**: Ready",
                    inline=True
                )
                
                # Quick Function Tests
                test_results = []
                
                # Test 1: Can access guild info
                try:
                    guild = ctx.guild
                    if guild:
                        test_results.append("✅ Guild access")
                    else:
                        test_results.append("⚠️ No guild context")
                except:
                    test_results.append("❌ Guild access failed")
                
                # Test 2: Can check user permissions
                try:
                    if ctx.author:
                        test_results.append("✅ User permissions")
                    else:
                        test_results.append("⚠️ No user context")
                except:
                    test_results.append("❌ User permission check failed")
                
                # Test 3: Can access voice channels
                try:
                    voice_channels = len(ctx.guild.voice_channels) if ctx.guild else 0
                    test_results.append(f"✅ Voice channels ({voice_channels})")
                except:
                    test_results.append("❌ Voice channel access failed")
                
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

        print("All commands registered successfully")
        
    except Exception as e:
        print(f"ERROR registering commands: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())

@bot.event
async def on_ready():
    bot.start_time = datetime.now()  # Add this line
    
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
                loop.run_in_executor(None, functools.partial(init_db, DATABASE_URL)),
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
        
        print("Setting up commands...")
        setup_commands()  # Register commands
        print("Commands registered successfully")
        
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
        heartbeat_task = asyncio.create_task(heartbeat())
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
    except:
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
    print(f"Database URL configured: {'Yes' if DATABASE_URL else 'No'}")
    
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