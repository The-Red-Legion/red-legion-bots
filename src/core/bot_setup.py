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
    # Note: Events are now handled in handlers/core.py
    # This function is kept for backwards compatibility
    pass


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
