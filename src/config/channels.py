"""
Channel configuration for Red Legion Discord Bot.
"""

from .settings import get_database_url

# Sunday Mining Configuration
# Note: Channel IDs are now managed in the database
# Use get_sunday_mining_channels() to retrieve current channels
SUNDAY_MINING_CHANNELS_FALLBACK = {
    'dispatch': '1385774416755163247',
    'alpha': '1386367354753257583',
    'bravo': '1386367395643449414',
    'charlie': '1386367464279478313',
    'delta': '1386368182421635224',
    'echo': '1386368221877272616',
    'foxtrot': '1386368253712375828'
}

def get_sunday_mining_channels(guild_id=None):
    """
    Get Sunday mining channels from database for a specific guild.
    Falls back to hardcoded values if database is unavailable.
    """
    try:
        from database import get_mining_channels_dict
        db_url = get_database_url()
        if db_url:
            channels = get_mining_channels_dict(db_url, guild_id)
            if channels:
                return channels
    except Exception as e:
        print(f"Warning: Could not get mining channels from database: {e}")
    
    # Fallback to hardcoded channels
    print("Using fallback mining channels")
    return SUNDAY_MINING_CHANNELS_FALLBACK
