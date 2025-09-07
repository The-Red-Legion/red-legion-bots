"""
Event management commands for the Red Legion Discord bot.

This module contains commands for managing organization events and participation tracking.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.decorators import has_org_role, standard_cooldown, error_handler
from event_handlers import start_logging, stop_logging, pick_winner, list_open_events


def register_commands(bot):
    """Register all event commands with the bot."""
    
    @bot.command(name="start_logging")
    @has_org_role()
    @error_handler
    async def start_logging_cmd(ctx):
        """Start logging participation for the current voice channel"""
        await start_logging(bot, ctx)

    @bot.command(name="stop_logging")
    @has_org_role()
    @error_handler
    async def stop_logging_cmd(ctx):
        """Stop logging participation for the current voice channel"""
        await stop_logging(bot, ctx)

    @bot.command(name="pick_winner")
    @has_org_role()
    @error_handler
    async def pick_winner_cmd(ctx):
        """Pick a random winner from current voice channel participants"""
        await pick_winner(bot, ctx)

    @bot.command(name="list_open_events")
    @has_org_role()
    @standard_cooldown()
    @error_handler
    async def list_open_events_cmd(ctx):
        """List all currently open events"""
        await list_open_events(bot, ctx)

    print("✅ Event commands registered")


async def setup(bot):
    """Setup function for discord.py extension loading."""
    register_commands(bot)
