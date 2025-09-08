"""
Admin commands module for Red Legion Discord Bot.
"""

from .core import register_commands

__all__ = [
    'register_commands'
]


async def setup(bot):
    """Setup function for discord.py extension loading."""
    register_commands(bot)
