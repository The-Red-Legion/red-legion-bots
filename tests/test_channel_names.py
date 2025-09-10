#!/usr/bin/env python3
"""
Quick test script to check what channel names are being returned
"""

import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.channels import get_sunday_mining_channels

def test_channel_names():
    print("=== Testing Channel Name Retrieval ===")
    
    # Test with guild ID (if available from database)
    guild_id = 814699481912049704  # Red Legion guild ID
    channels = get_sunday_mining_channels(guild_id)
    
    print(f"Guild ID: {guild_id}")
    print(f"Retrieved channels: {channels}")
    print()
    
    for channel_name, channel_id in channels.items():
        should_join = 'dispatch' in channel_name.lower()
        print(f"Channel: '{channel_name}'")
        print(f"  Lowercase: '{channel_name.lower()}'")
        print(f"  Contains 'dispatch': {should_join}")
        print(f"  Channel ID: {channel_id}")
        print()

if __name__ == "__main__":
    test_channel_names()
