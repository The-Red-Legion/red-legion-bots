#!/usr/bin/env python3
"""
Test script for the Discord Bot Web API

This script starts the web API server for testing purposes.
In production, this would be integrated with the main bot.
"""

import asyncio
import uvicorn
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from web_api import app

def main():
    """Run the Discord Bot Web API server."""
    print("🚀 Starting Discord Bot Web API for testing...")
    print("📡 API will be available at http://localhost:8001")
    print("⚠️ Note: Discord integration will not work without the actual bot running")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        log_level="info",
        reload=True
    )

if __name__ == "__main__":
    main()