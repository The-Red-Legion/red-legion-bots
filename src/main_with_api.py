#!/usr/bin/env python3
"""
Enhanced main entry point for Red Legion Discord Bot with Web API integration.

This version starts both the Discord bot and the web API server concurrently,
allowing the web interface to trigger Discord bot actions directly.
"""

import sys
import os
import logging
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from bot import RedLegionBot
from database_init import init_database_for_deployment
from config.settings import get_database_url

def setup_logging():
    """Set up logging to both console and file."""
    try:
        # Create a logger
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # Create formatters
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Console handler (existing behavior)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        print("✅ Logging configured for console output")
        logging.info("Red Legion Bot with Web API logging initialized")
        
    except Exception as e:
        print(f"⚠️ Could not setup logging: {e}")

def create_pid_file():
    """Create a PID file for process monitoring."""
    try:
        pid_file = f"/tmp/red_legion_bot_api_{os.getpid()}.pid"
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
        print(f"✅ PID file created: {pid_file}")
        return pid_file
    except Exception as e:
        print(f"⚠️ Could not create PID file: {e}")
        return None

def remove_pid_file(pid_file):
    """Remove the PID file."""
    try:
        if pid_file and os.path.exists(pid_file):
            os.remove(pid_file)
            print(f"✅ PID file removed: {pid_file}")
    except Exception as e:
        print(f"⚠️ Could not remove PID file: {e}")

async def main():
    """Initialize and run the Red Legion Discord Bot with Web API."""
    print("🚀 Starting Red Legion Discord Bot with Web API integration...")
    print("=" * 60)
    
    # Setup logging first
    setup_logging()
    
    # Create PID file for monitoring
    pid_file = create_pid_file()
    
    # Initialize database
    try:
        db_url = get_database_url()
        if not db_url:
            print("❌ Database URL not configured")
            logging.error("Database URL not configured")
            remove_pid_file(pid_file)
            return
        
        print("📊 Initializing database...")
        logging.info("Initializing database...")
        
        # Initialize database
        if init_database_for_deployment():
            print("✅ Database initialized successfully")
            logging.info("Database initialized successfully")
        else:
            print("❌ Database initialization failed")
            logging.error("Database initialization failed")
            remove_pid_file(pid_file)
            return
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        logging.error(f"Database initialization failed: {e}")
        remove_pid_file(pid_file)
        return
    
    # Create and run bot with web API
    try:
        logging.info("Starting Red Legion Discord Bot with Web API...")
        bot = RedLegionBot()
        
        print("🤖 Bot instance created successfully")
        print("🌐 Starting combined bot + web API server...")
        print("📡 Web API will be available at http://localhost:8001")
        print("🎤 Discord bot will connect to Discord")
        print("=" * 60)
        
        # Start bot with web API integration
        await bot.start_with_web_api()
        
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal, shutting down...")
        logging.info("Bot shutdown initiated by user")
        
    except Exception as e:
        print(f"❌ Error running bot with web API: {e}")
        logging.error(f"Bot runtime error: {e}")
        import traceback
        logging.error(f"Full traceback: {traceback.format_exc()}")
        
    finally:
        remove_pid_file(pid_file)
        print("👋 Red Legion Bot with Web API shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Shutdown complete")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)