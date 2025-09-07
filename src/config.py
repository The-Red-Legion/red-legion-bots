"""
Legacy configuration module (Compatibility)

This file exists for backward compatibility. 
All configuration is now in config/settings.py
"""

import warnings
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Show deprecation warning
warnings.warn(
    "config.py is deprecated. Use config.settings instead.", 
    DeprecationWarning, 
    stacklevel=2
)

# Import everything from the new config module for compatibility
from config.settings import *
from config.channels import *