"""
Legacy config module for backward compatibility.
This file re-exports the new modular configuration.
"""

from .config.settings import *
from .config.channels import *

# Legacy exports for backward compatibility
DISCORD_TOKEN = DISCORD_CONFIG['TOKEN']