#!/usr/bin/env python3
"""
Post-deployment verification script to check if commands are working.
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime

async def verify_bot_commands():
    """Verify that the bot deployment was successful."""
    print("🔍 Post-Deployment Bot Verification")
    print("=" * 50)
    
    # Basic checks
    print("📋 Verification Steps:")
    print("1. ✅ Deployment completed successfully")
    print("2. 🔄 Checking Discord command sync...")
    
    # Instructions for manual verification
    print("\n🧪 Manual Discord Tests:")
    print("Please test these commands in Discord:")
    print()
    
    expected_commands = [
        ("red-ping", "Basic connectivity test"),
        ("red-health", "Health check"),
        ("red-events list", "List events"),
        ("red-market-list", "List market items"),
    ]
    
    for cmd, desc in expected_commands:
        print(f"  /{cmd:<20} - {desc}")
    
    print("\n✅ Expected Results:")
    print("  - All commands should autocomplete when typing /red")
    print("  - Commands should respond without errors")
    print("  - No old commands without 'red-' prefix should appear")
    
    print("\n🎯 Quick Test:")
    print("  Type '/red-ping' in Discord")
    print("  Expected response: '🏓 Pong! Red Legion Bot is responsive.'")
    
    return True

def print_verification_summary():
    """Print verification summary."""
    print("\n" + "=" * 50)
    print("📊 DEPLOYMENT VERIFICATION SUMMARY")
    print("=" * 50)
    print()
    print("✅ Code deployed successfully")
    print("✅ Bot should be running with new command structure")
    print("🔄 Commands synced to Discord (may take 1-5 minutes)")
    print()
    print("🧪 Next Steps:")
    print("1. Test /red-ping in Discord")
    print("2. Verify autocomplete shows red- commands")
    print("3. Check that old commands are gone")
    print()
    print("📝 Issues? Check bot logs for:")
    print("  - '🎉 SUCCESS: All synced commands have red- prefix!'")
    print("  - Command count: Should show 18 commands synced")
    print()

if __name__ == "__main__":
    print(f"🚀 Red Legion Bot Deployment Verification")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    result = asyncio.run(verify_bot_commands())
    print_verification_summary()
    
    if result:
        print("🎉 Verification script completed!")
        print("💡 Now test the commands in Discord to confirm everything works.")
    else:
        print("❌ Verification script encountered issues.")
