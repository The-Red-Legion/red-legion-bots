"""
Main entry point for Red Legion Discord Bot.
"""

import sys
import os
import logging
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
        
        # File handler for deployment monitoring
        log_file = "/app/bot.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO) 
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        print(f"✅ Logging configured - Console + File: {log_file}")
        logging.info("Red Legion Bot logging initialized")
        
    except Exception as e:
        print(f"⚠️ Could not setup file logging: {e}")

def create_pid_file():
    """Create a PID file for process monitoring."""
    try:
        pid_file = "/app/bot.pid"
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
        print(f"✅ Created PID file: {pid_file} (PID: {os.getpid()})")
        logging.info(f"Created PID file: {pid_file} (PID: {os.getpid()})")
    except Exception as e:
        print(f"⚠️ Could not create PID file: {e}")

def remove_pid_file():
    """Remove the PID file on shutdown."""
    try:
        pid_file = "/app/bot.pid"
        if os.path.exists(pid_file):
            os.remove(pid_file)
            print(f"✅ Removed PID file: {pid_file}")
            logging.info(f"Removed PID file: {pid_file}")
    except Exception as e:
        print(f"⚠️ Could not remove PID file: {e}")

def main():
    """Initialize and run the Red Legion Discord Bot."""
    print("🚀 Starting Red Legion Discord Bot...")
    
    # Setup logging first
    setup_logging()
    
    # Create PID file for monitoring
    create_pid_file()
    
    # Initialize database
    try:
        db_url = get_database_url()
        if not db_url:
            print("❌ Database URL not configured")
            logging.error("Database URL not configured")
            remove_pid_file()
            return
        
        print("📊 Initializing database...")
        logging.info("Initializing database...")
        print(f"📋 Database URL (masked): {db_url[:30]}...{db_url[-20:] if len(db_url) > 50 else db_url}")
        print(f"🔍 URL contains '#': {'#' in db_url}")
        print(f"🔍 URL contains '%23': {'%23' in db_url}")
        
        # Initialize database
        if init_database_for_deployment():
            print("✅ Database initialized successfully")
            logging.info("Database initialized successfully")
        else:
            print("❌ Database initialization failed")
            logging.error("Database initialization failed")
            remove_pid_file()
            return
        print("✅ Database initialized successfully")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        logging.error(f"Database initialization failed: {e}")
        remove_pid_file()
        return
    
    # Create and run bot
    try:
        logging.info("Starting Red Legion Discord Bot...")
        bot = RedLegionBot()
        bot.run_bot()
        
    except KeyboardInterrupt:
        print("\n🛑 Bot shutdown requested")
        logging.info("Bot shutdown requested by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")
        logging.error(f"Bot error: {e}")
        raise
    finally:
        print("👋 Red Legion Bot shutting down...")
        logging.info("Red Legion Bot shutting down...")
        remove_pid_file()

if __name__ == "__main__":
    main()
