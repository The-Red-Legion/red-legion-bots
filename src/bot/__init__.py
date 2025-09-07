"""
Bot module for Red Legion Discord Bot.
"""

from .client import RedLegionBot
from .utils import format_duration, format_currency

__all__ = [
    'RedLegionBot',
    'format_duration',
    'format_currency'
]
