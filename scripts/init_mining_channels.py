#!/usr/bin/env python3
"""
Initialize mining channels in the database.
This script sets up the default Sunday mining channels.
"""

import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.config import get_database_url, SUNDAY_MINING_CHANNELS_FALLBACK
from src.database import add_mining_channel

def initialize_mining_channels(guild_id=None):
    """Initialize the default mining channels in the database for a specific guild."""
    if not guild_id:
        print("❌ Guild ID is required for channel initialization")
        return False
        
    print(f"🚀 Initializing Sunday mining channels for guild {guild_id}...")
    
    try:
        db_url = get_database_url()
        if not db_url:
            print("❌ Database URL not available")
            return False
        
        # Channel descriptions
        channel_descriptions = {
            'dispatch': 'Main coordination channel for Sunday mining operations',
            'alpha': 'Alpha squad mining operations',
            'bravo': 'Bravo squad mining operations', 
            'charlie': 'Charlie squad mining operations',
            'delta': 'Delta squad mining operations',
            'echo': 'Echo squad mining operations',
            'foxtrot': 'Foxtrot squad mining operations'
        }
        
        success_count = 0
        for channel_name, channel_id in SUNDAY_MINING_CHANNELS_FALLBACK.items():
            try:
                description = channel_descriptions.get(channel_name, f"{channel_name.title()} mining channel")
                add_mining_channel(db_url, guild_id, channel_id, channel_name.title(), description)
                print(f"✅ Added {channel_name.title()} (ID: {channel_id}) to guild {guild_id}")
                success_count += 1
            except Exception as e:
                print(f"❌ Failed to add {channel_name}: {e}")
        
        print(f"\n🎉 Successfully initialized {success_count}/{len(SUNDAY_MINING_CHANNELS_FALLBACK)} mining channels!")
        return success_count == len(SUNDAY_MINING_CHANNELS_FALLBACK)
        
    except Exception as e:
        print(f"❌ Error initializing mining channels: {e}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        try:
            guild_id = int(sys.argv[1])
            initialize_mining_channels(guild_id)
        except ValueError:
            print("❌ Guild ID must be a valid integer")
            print("Usage: python init_mining_channels.py <guild_id>")
    else:
        print("❌ Usage: python init_mining_channels.py <guild_id>")
        print("Example: python init_mining_channels.py 123456789012345678")
