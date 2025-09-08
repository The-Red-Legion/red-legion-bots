"""
Decorators for the Red Legion Discord Bot.
"""

from functools import wraps

def retry_db_operation(max_retries=3):
    """Decorator to retry database operations on failure."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    print(f"Database operation failed (attempt {attempt + 1}): {e}")
            return None
        return wrapper
    return decorator
