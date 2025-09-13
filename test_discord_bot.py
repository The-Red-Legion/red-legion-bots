#!/usr/bin/env python3
"""
Test script for Discord bot voice channel functionality.
Tests if the bot can join and leave the Stream/Restricted channel.
"""

import asyncio
import aiohttp
import json
import time

# Stream/Restricted channel ID
STREAM_RESTRICTED_CHANNEL_ID = "814699481912049709"
BOT_API_URL = "http://35.192.203.184:8001"

async def test_bot_connection():
    """Test if the bot API is accessible."""
    print("🔗 Testing bot API connection...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BOT_API_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Bot API connected: {data}")
                    return True
                else:
                    print(f"❌ Bot API returned status {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Failed to connect to bot API: {e}")
        return False

async def test_bot_status():
    """Get bot status."""
    print("📊 Getting bot status...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BOT_API_URL}/bot/status") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Bot status: {json.dumps(data, indent=2)}")
                    return data
                else:
                    print(f"❌ Bot status returned status {response.status}")
                    return None
    except Exception as e:
        print(f"❌ Failed to get bot status: {e}")
        return None

async def test_join_voice_channel():
    """Test joining the Stream/Restricted channel."""
    print(f"🎤 Testing join voice channel {STREAM_RESTRICTED_CHANNEL_ID}...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BOT_API_URL}/test/voice/{STREAM_RESTRICTED_CHANNEL_ID}/join") as response:
                data = await response.json()
                if response.status == 200 and data.get('success'):
                    print(f"✅ Successfully joined voice channel: {data['message']}")
                    return True
                else:
                    print(f"❌ Failed to join voice channel: {data}")
                    return False
    except Exception as e:
        print(f"❌ Error joining voice channel: {e}")
        return False

async def test_leave_voice_channel():
    """Test leaving the Stream/Restricted channel."""
    print(f"🔇 Testing leave voice channel {STREAM_RESTRICTED_CHANNEL_ID}...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BOT_API_URL}/test/voice/{STREAM_RESTRICTED_CHANNEL_ID}/leave") as response:
                data = await response.json()
                if response.status == 200 and data.get('success'):
                    print(f"✅ Successfully left voice channel: {data['message']}")
                    return True
                else:
                    print(f"❌ Failed to leave voice channel: {data}")
                    return False
    except Exception as e:
        print(f"❌ Error leaving voice channel: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting Discord Bot API Tests")
    print("=" * 50)
    
    # Test 1: Bot API connection
    if not await test_bot_connection():
        print("❌ Cannot proceed without bot API connection")
        return
    
    print()
    
    # Test 2: Bot status
    status = await test_bot_status()
    if not status or not status.get('connected'):
        print("❌ Bot is not connected to Discord")
        return
    
    print()
    
    # Test 3: Join voice channel
    if await test_join_voice_channel():
        print("⏱️ Waiting 10 seconds in voice channel...")
        await asyncio.sleep(10)
        
        # Test 4: Leave voice channel
        await test_leave_voice_channel()
    
    print()
    print("🏁 Tests completed!")

if __name__ == "__main__":
    asyncio.run(main())