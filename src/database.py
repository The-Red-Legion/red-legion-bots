"""
Legacy database module (Compatibility)

This file exists for backward compatibility.
All database operations are now in database/operations.py
"""

import warnings
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Show deprecation warning
warnings.warn(
    "database.py is deprecated. Use database.operations instead.", 
    DeprecationWarning, 
    stacklevel=2
)

# Import everything from the new database modules for compatibility
from database.operations import *
from database.models import *
from database import init_database as init_db