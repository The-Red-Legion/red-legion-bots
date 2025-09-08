"""
Bot utilities and helper functions.
"""

def format_duration(seconds):
    """Format duration in seconds to human readable format."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {remaining_seconds}s"
    elif minutes > 0:
        return f"{minutes}m {remaining_seconds}s"
    else:
        return f"{remaining_seconds}s"

def format_currency(amount):
    """Format currency amount with proper formatting."""
    return f"{amount:,.2f} aUEC"
