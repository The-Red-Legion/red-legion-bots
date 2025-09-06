"""
Shared decorators and utilities for the Red Legion Discord bot commands.
"""

from discord.ext import commands
from functools import wraps


def has_org_role():
    """
    Decorator to check if user has organization role.
    Currently returns True for testing - should be updated with real role check.
    
    Returns:
        commands.check: Discord.py command check decorator
    """
    async def predicate(ctx):
        # TODO: Implement actual role checking logic
        # For now, allow all users for testing
        return True
    return commands.check(predicate)


def standard_cooldown(rate=1, per=30.0, bucket_type=commands.BucketType.guild):
    """
    Standard cooldown decorator for commands.
    
    Args:
        rate: Number of times command can be used
        per: Time period in seconds
        bucket_type: Type of cooldown bucket
        
    Returns:
        commands.cooldown: Discord.py cooldown decorator
    """
    return commands.cooldown(rate, per, bucket_type)


def admin_only():
    """
    Decorator to restrict commands to administrators only.
    
    Returns:
        commands.check: Discord.py command check decorator
    """
    async def predicate(ctx):
        # Check if user has administrator permissions
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)


def error_handler(func):
    """
    Decorator to handle common command errors gracefully.
    
    Args:
        func: The command function to wrap
        
    Returns:
        function: Wrapped function with error handling
    """
    @wraps(func)
    async def wrapper(ctx, *args, **kwargs):
        try:
            return await func(ctx, *args, **kwargs)
        except Exception as e:
            await ctx.send(f"⚠️ An error occurred: {str(e)}")
            print(f"Error in command {func.__name__}: {e}")
            import traceback
            traceback.print_exc()
    return wrapper
