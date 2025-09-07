"""
Event management commands for the Red Legion Discord bot.

This module contains commands for managing organization events and participation tracking.

Legacy event commands - replaced by new modular mining system.
These commands are disabled as they reference the old event_handlers module.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.decorators import has_org_role, standard_cooldown, error_handler
# Legacy import - disabled
# from event_handlers import start_logging, stop_logging, pick_winner, list_open_events


def register_commands(bot):
    """Register all event commands with the bot."""
    
    # Legacy commands disabled - use new /sunday_mining_start, /sunday_mining_stop, /payroll instead
    print("⚠️ Legacy event commands disabled - use new mining commands instead")
    
    @bot.command(name="start_logging")
    @has_org_role()
    @error_handler
    async def start_logging_cmd(ctx):
        """Start logging participation for the current voice channel"""
        await ctx.send("⚠️ This command has been replaced by `/sunday_mining_start`. Use the new slash command for mining operations.")

    @bot.command(name="stop_logging")
    @has_org_role()
    @error_handler
    async def stop_logging_cmd(ctx):
        """Stop logging participation for the current voice channel"""
        await ctx.send("⚠️ This command has been replaced by `/sunday_mining_stop`. Use the new slash command for mining operations.")

    @bot.command(name="pick_winner")
    @has_org_role()
    @error_handler
    async def pick_winner_cmd(ctx):
        """Pick a random winner from current voice channel participants"""
        await ctx.send("⚠️ This legacy command is disabled. Winner selection functionality is now integrated into the new mining system.")

    @bot.command(name="list_open_events")
    @has_org_role()
    @standard_cooldown()
    @error_handler
    async def list_open_events_cmd(ctx):
        """List all currently open events"""
        await ctx.send("⚠️ This command has been replaced by `/payroll calculate`. Use the new slash command to view and process mining events.")

    print("✅ Event commands registered")


async def setup(bot):
    """Setup function for discord.py extension loading."""
    register_commands(bot)
