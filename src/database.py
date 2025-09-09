"""
Legacy database module for backward compatibility.
This file re-exports the new modular database functions.
"""

from .database.schemas import init_database as init_db
from .database.operations import *
from .database.models import *

# Legacy function name mapping (keeping both names available)
init_database = init_db