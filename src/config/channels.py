"""
Channel configuration for Red Legion Discord Bot.
"""

from .settings import get_database_url
from database.connection import resolve_database_url

# Sunday Mining Configuration
# Note: Channel IDs are now managed in the database
# Use get_sunday_mining_channels() to retrieve current channels
SUNDAY_MINING_CHANNELS_FALLBACK = {
    'Dispatch/Main': '1385774416755163247',
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
        # Direct database query approach to bypass import issues
        import psycopg2
        from urllib.parse import urlparse
        
        db_url = get_database_url()
        if db_url:
            # If no guild_id provided, use the default Red Legion guild ID
            if guild_id is None:
                guild_id = 814699481912049704  # Default Red Legion server ID
                
            # Connect using URL resolution for Cloud SQL
            resolved_url = resolve_database_url(db_url)
            conn = psycopg2.connect(resolved_url)
                
            c = conn.cursor()
            c.execute('''
                SELECT channel_name, channel_id 
                FROM mining_channels 
                WHERE guild_id = %s AND is_active = TRUE
                ORDER BY channel_name
            ''', (guild_id,))
            
            rows = c.fetchall()
            
            if rows:
                channels_dict = {}
                for channel_name, channel_id in rows:
                    channels_dict[channel_name] = str(channel_id)
                
                conn.close()
                print(f"✅ Loaded {len(channels_dict)} mining channels from database for guild {guild_id}")
                return channels_dict
            
            conn.close()
            
    except Exception as e:
        print(f"Warning: Could not get mining channels from database: {e}")
    
    # Fallback to hardcoded channels
    print("Using fallback mining channels")
    return SUNDAY_MINING_CHANNELS_FALLBACK
