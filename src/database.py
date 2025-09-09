"""
Legacy database module for backward compatibility.
This file re-exports the new modular database functions.
"""

from database import init_database as init_db
from database.operations import *
from database.models import *

# Legacy function name mapping
def init_database():
    """Legacy function name for backward compatibility."""
    return init_db()