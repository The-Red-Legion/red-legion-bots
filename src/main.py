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
from config import get_database_url

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
