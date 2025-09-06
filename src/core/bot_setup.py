"""
Bot setup and initialization utilities for the Red Legion Discord bot.
"""

import discord
from discord.ext import commands
import datetime


def create_bot_instance():
    """
    Create and configure the Discord bot instance with proper intents.
    
    Returns:
        commands.Bot: Configured bot instance
    """
    intents = discord.Intents.default()
    intents.members = True
    intents.voice_states = True
    intents.message_content = True
    
    bot = commands.Bot(command_prefix='!', intents=intents)
    return bot


async def setup_bot_events(bot):
    """
    Set up common bot event handlers.
    
    Args:
        bot: The Discord bot instance
    """
    
    @bot.event
    async def on_ready():
        bot.start_time = datetime.datetime.now()
        
        print(f'Logged in as {bot.user}')
        print(f'Bot is ready and connected to {len(bot.guilds)} servers')
        print(f"🤖 {bot.user} has connected to Discord!")
        print(f"📅 Bot started at: {bot.start_time}")
        print(f"🏠 Connected to {len(bot.guilds)} guilds")
        
        # Log guild information
        for guild in bot.guilds:
            print(f'Connected to guild: {guild.name} (ID: {guild.id})')

    @bot.event
    async def on_error(event, *args, **kwargs):
        print(f'DISCORD EVENT ERROR in event {event}')
        print(f'Args: {args}')
        print(f'Kwargs: {kwargs}')
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())

    @bot.event
    async def on_command_error(ctx, error):
        print(f'COMMAND ERROR in command {ctx.command}: {error}')
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        try:
            await ctx.send(f"⚠️ Command error: {str(error)}")
        except Exception:
            pass

    @bot.event
    async def on_disconnect():
        print("⚠️  Bot disconnected from Discord!")

    @bot.event
    async def on_resumed():
        print("✅ Bot resumed connection to Discord!")


async def setup_heartbeat(bot):
    """
    Set up a heartbeat task to monitor bot health.
    
    Args:
        bot: The Discord bot instance
    """
    import asyncio
    
    async def heartbeat():
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            print(f"💓 Heartbeat: Bot is still running at {datetime.datetime.now()}")
    
    # Start heartbeat task
    bot.heartbeat_task = asyncio.create_task(heartbeat())
    print("Heartbeat monitoring started")
