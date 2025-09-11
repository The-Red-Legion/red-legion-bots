"""
Mining commands module for Red Legion Discord Bot.
"""

from .core import SundayMiningCommands, PayrollCalculationModal, EventSelectionView, register_commands

__all__ = [
    'SundayMiningCommands',
    'PayrollCalculationModal',
    'EventSelectionView',
    'register_commands'
]


async def setup(bot):
    """Setup function for discord.py extension loading."""
    await bot.add_cog(SundayMiningCommands(bot))
    # Also register legacy commands for compatibility
    register_commands(bot)
