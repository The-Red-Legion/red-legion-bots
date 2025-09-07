"""
Config module initialization with explicit imports.
"""

from .settings import (
    get_database_url,
    ORE_TYPES,
    UEX_API_CONFIG,
    DISCORD_CONFIG,
    validate_config
)
from .channels import (
    get_sunday_mining_channels,
    SUNDAY_MINING_CHANNELS_FALLBACK
)

__all__ = [
    'get_database_url',
    'get_sunday_mining_channels',
    'SUNDAY_MINING_CHANNELS_FALLBACK',
    'ORE_TYPES',
    'UEX_API_CONFIG',
    'DISCORD_CONFIG',
    'validate_config'
]
