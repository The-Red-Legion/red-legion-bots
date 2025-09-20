"""
Payroll UI Components - DEPRECATED

These Discord UI components are deprecated as of the Management Portal integration.
All payroll functionality has been moved to the web interface.

Components included (for backwards compatibility):
- Event selection views
- Collection input modals
- Confirmation and summary views
"""

# DEPRECATED: These imports are kept for compatibility but functionality
# has been moved to the Management Portal web interface
from .modals import MiningCollectionModal, SalvageCollectionModal
from .views import EventSelectionView, PayrollConfirmationView

__all__ = [
    'MiningCollectionModal',
    'SalvageCollectionModal',
    'EventSelectionView',
    'PayrollConfirmationView',
]