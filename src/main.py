"""
Main entry point for Red Legion Discord Bot.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from bot import RedLegionBot
from database import init_database
from config.settings import get_database_url

async def main():
    """Initialize and run the Red Legion Discord Bot."""
    print("🚀 Starting Red Legion Discord Bot...")
    
    # Initialize database
    try:
        db_url = get_database_url()
        if not db_url:
            print("❌ Database URL not configured")
            return
        
        print("📊 Initializing database...")
        print(f"📋 Database URL (masked): {db_url[:30]}...{db_url[-20:] if len(db_url) > 50 else db_url}")
        print(f"🔍 URL contains '#': {'#' in db_url}")
        print(f"🔍 URL contains '%23': {'%23' in db_url}")
        init_database(db_url)
        print("✅ Database initialized successfully")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return
    
    # Create and run bot
    try:
        bot = RedLegionBot()
        await bot.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Bot shutdown requested")
    except Exception as e:
        print(f"❌ Bot error: {e}")
        raise
    finally:
        print("👋 Red Legion Bot shutting down...")

if __name__ == "__main__":
    asyncio.run(main())
