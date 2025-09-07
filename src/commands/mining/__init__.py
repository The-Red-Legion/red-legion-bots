"""
Mining commands module for Red Legion Discord Bot.
"""

from .core import *

__all__ = [
    'SundayMiningCommands',
    'PayrollCalculationModal',
    'EventSelectionView'
]


async def setup(bot):
    """Setup function for discord.py extension loading."""
    await bot.add_cog(SundayMiningCommands(bot))
