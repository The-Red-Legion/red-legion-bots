"""
Red Legion Discord Bot - Main Entry Point

This is the main bot file that initializes and runs the Red Legion Discord bot.
The bot now uses a modular architecture with feature-specific command modules.
"""

import datetime
import asyncio

# Import configuration and database utilities
from .config import DISCORD_TOKEN, get_database_url
from .database import init_db

# Import our new modular components
from .core.bot_setup import create_bot_instance, setup_heartbeat
from .commands import register_all_commands
from .handlers.voice_tracking import start_voice_tracking
from .event_handlers import setup_event_handlers

# Create bot instance using our core setup
bot = create_bot_instance()


def setup_commands():
    """Set up all commands using our modular system."""
    try:
        print("🔧 Registering commands from modular system...")
        
        # Register all commands from our modular command system
        register_all_commands(bot)
        
        print("✅ All commands registered successfully from modular system")
        
    except Exception as e:
        print(f"❌ ERROR registering commands: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())


@bot.event
async def on_ready():
    """Handle bot ready event with comprehensive setup."""
    bot.start_time = datetime.datetime.now()
    
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
        import functools
        loop = asyncio.get_event_loop()
        
        # Add timeout to database initialization to prevent hanging
        try:
            await asyncio.wait_for(
                loop.run_in_executor(None, functools.partial(init_db, get_database_url())),
                timeout=30.0  # 30 second timeout
            )
            print("✅ Database initialized successfully")
        except asyncio.TimeoutError:
            print("⚠️ Database initialization timed out after 30 seconds - continuing anyway")
        except Exception as db_error:
            print(f"⚠️ Database initialization failed: {db_error} - bot will continue without database")
        
        print("Setting up event handlers...")
        await setup_event_handlers()
        print("✅ Event handlers registered successfully")
        
        # Start voice tracking
        start_voice_tracking()
        
        print("Bot setup completed successfully!")
        print("Bot is fully operational and ready to receive commands")
        
        # Start heartbeat monitoring
        await setup_heartbeat(bot)
        
    except Exception as e:
        print(f"CRITICAL ERROR during setup: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        print("Bot will attempt to continue running despite setup errors...")


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


if __name__ == "__main__":
    print("🚀 Starting Red Legion Discord Bot...")
    print(f"Discord token length: {len(DISCORD_TOKEN) if DISCORD_TOKEN else 'None'}")
    print(f"Database URL configured: {'Yes' if get_database_url() else 'No'}")
    
    # Register commands before starting the bot
    print("Setting up commands...")
    setup_commands()
    print("Commands setup complete")
    
    try:
        print("🎯 Starting bot with modular architecture...")
        bot.run(DISCORD_TOKEN)
        print("bot.run() returned - this should not happen unless bot stops")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to start bot: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
    finally:
        print("Bot execution finished")
