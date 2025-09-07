"""
Event handlers for the Red Legion Discord bot.

This package contains:
- voice_tracking.py: Voice channel participation tracking
- core.py: Basic Discord event handlers
"""

from .voice_tracking import (
    on_voice_state_update,
    get_member_mining_summary,
    get_all_mining_participants,
    reset_mining_session,
    log_members,
    start_voice_tracking,
    disconnect_from_all_channels,
    stop_voice_tracking,
    set_bot_instance,
    join_voice_channel,
    leave_voice_channel,
    add_tracked_channel,
    remove_tracked_channel,
    get_tracking_status,
    setup
)
from .core import setup_core_handlers

__all__ = [
    'on_voice_state_update',
    'get_member_mining_summary',
    'get_all_mining_participants', 
    'reset_mining_session',
    'log_members',
    'start_voice_tracking',
    'disconnect_from_all_channels',
    'stop_voice_tracking',
    'set_bot_instance',
    'join_voice_channel',
    'leave_voice_channel',
    'add_tracked_channel',
    'remove_tracked_channel',
    'get_tracking_status',
    'setup',
    'setup_core_handlers'
]
