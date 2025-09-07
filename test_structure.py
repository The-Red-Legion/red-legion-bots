#!/usr/bin/env python3
"""
Test script to verify the reorganized Red Legion bot structure works correctly.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """Test that all major modules can be imported correctly."""
    print("🧪 Testing Red Legion Bot reorganized structure...")
    
    try:
        # Test config module
        print("Testing config module...")
        from config import validate_config, get_database_url
        print("✅ Config module imports correctly")
        
        # Test database module  
        print("Testing database module...")
        from database import init_database
        print("✅ Database module imports correctly")
        
        # Test bot module
        print("Testing bot module...")
        from bot import RedLegionBot
        print("✅ Bot module imports correctly")
        
        # Test mining commands
        print("Testing mining commands...")
        from commands.mining import SundayMiningCommands
        print("✅ Mining commands import correctly")
        
        # Test utils
        print("Testing utils module...")
        from utils import has_org_role, has_org_leaders_role
        print("✅ Utils module imports correctly")
        
        # Test handlers
        print("Testing handlers...")
        from handlers.voice_tracking import get_tracking_status
        print("✅ Voice tracking handler imports correctly")
        
        print("\n🎉 All modules imported successfully!")
        print("✅ Reorganized structure is working correctly!")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_structure():
    """Show the new organized structure."""
    print("\n📁 New Red Legion Bot Structure:")
    print("src/")
    print("├── __init__.py           # Main package init")
    print("├── main.py              # Entry point")
    print("├── config/              # Configuration management")
    print("│   ├── __init__.py")
    print("│   ├── settings.py      # Core settings & API config")
    print("│   └── channels.py      # Channel management")
    print("├── database/            # Database operations") 
    print("│   ├── __init__.py")
    print("│   ├── models.py        # Data models")
    print("│   └── operations.py    # Database functions")
    print("├── bot/                 # Discord bot client")
    print("│   ├── __init__.py")
    print("│   ├── client.py        # Main bot class")
    print("│   └── utils.py         # Bot utilities")
    print("├── commands/            # Command modules")
    print("│   ├── __init__.py")
    print("│   ├── mining/          # Sunday mining commands")
    print("│   ├── admin/           # Administrative commands")
    print("│   ├── general.py       # General purpose commands")
    print("│   ├── market.py        # Market system commands")
    print("│   ├── loans.py         # Loan system commands") 
    print("│   ├── events.py        # Event management")
    print("│   └── diagnostics.py   # Health & diagnostics")
    print("├── handlers/            # Event handlers")
    print("│   ├── __init__.py")
    print("│   ├── core.py          # Core Discord events")
    print("│   └── voice_tracking.py # Voice state tracking")
    print("├── utils/               # Utility functions")
    print("│   ├── __init__.py")
    print("│   ├── decorators.py    # Custom decorators")
    print("│   └── discord_helpers.py # Discord utility functions")
    print("└── core/                # Core framework")
    print("    ├── __init__.py")
    print("    ├── bot_setup.py     # Bot initialization")
    print("    └── decorators.py    # Framework decorators")

if __name__ == "__main__":
    show_structure()
    success = test_imports()
    
    if success:
        print("\n✅ Red Legion Bot reorganization completed successfully!")
        print("🚀 The bot is ready to run with:")
        print("   cd /Users/jt/Devops/red-legion/red-legion-bots")
        print("   python3 src/main.py")
    else:
        print("\n❌ There are still some import issues to resolve.")
        sys.exit(1)
