"""
Configuration module for Red Legion Discord Bot.
"""

from .settings import *
from .channels import *

__all__ = [
    'get_database_url',
    'get_sunday_mining_channels',
    'SUNDAY_MINING_CHANNELS_FALLBACK',
    'ORE_TYPES',
    'UEX_API_CONFIG',
    'DISCORD_CONFIG'
]
