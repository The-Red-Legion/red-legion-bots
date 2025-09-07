"""
Core Discord event handlers for the Red Legion Discord bot.

This module contains basic Discord event handlers that don't fit in other specific categories.
"""

from datetime import datetime


async def setup_core_handlers(bot):
    """
    Set up core Discord event handlers.
    
    Args:
        bot: The Discord bot instance
    """
    
    @bot.event
    async def on_ready():
        """Handle bot ready event with comprehensive setup."""
        bot.start_time = datetime.now()
        
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
            from ..database import init_db
            from ..config.settings import get_database_url
            
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
            from ..event_handlers import setup_event_handlers
            await setup_event_handlers()  # Register event handler
            print("Event handlers registered successfully")
            
            print("Bot setup completed successfully!")
            print("Bot is fully operational and ready to receive commands")
            
            # Add a simple heartbeat to ensure bot stays alive and log activity
            print("✅ Bot startup sequence completed - bot should remain running")
            
            # Start a simple heartbeat task to verify bot is still alive
            async def heartbeat():
                while True:
                    await asyncio.sleep(300)  # Every 5 minutes
                    print(f"💓 Heartbeat: Bot is still running at {datetime.now()}")
            
            # Start heartbeat task
            bot.heartbeat_task = asyncio.create_task(heartbeat())  # Store reference to prevent GC
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
        """Handle Discord API errors gracefully."""
        print(f'DISCORD EVENT ERROR in event {event}')
        print(f'Args: {args}')
        print(f'Kwargs: {kwargs}')
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        # DO NOT re-raise the exception - let the bot continue running

    @bot.event
    async def on_command_error(ctx, error):
        """Handle command errors gracefully."""
        print(f'COMMAND ERROR in command {ctx.command}: {error}')
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        # Send error message to user but don't crash
        try:
            await ctx.send(f"⚠️ Command error: {str(error)}")
        except Exception:
            pass  # Don't crash if we can't send the error message

    @bot.event
    async def on_disconnect():
        """Log when bot disconnects from Discord."""
        print("⚠️ Bot disconnected from Discord!")

    @bot.event
    async def on_resumed():
        """Log when bot reconnects to Discord."""
        print("✅ Bot resumed connection to Discord!")

    print("✅ Core event handlers registered")


async def setup(bot):
    """Setup function for discord.py extension loading."""
    await setup_core_handlers(bot)
