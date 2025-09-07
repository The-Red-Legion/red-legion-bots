"""
Legacy participation bot module (Compatibility)

This file exists for backward compatibility.
The bot entry point is now src/main.py
"""

import warnings
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Show deprecation warning
warnings.warn(
    "participation_bot.py is deprecated. Use main.py instead.", 
    DeprecationWarning, 
    stacklevel=2
)

# Legacy compatibility - redirect to new main entry point
async def main():
    """Legacy main function - redirects to new entry point."""
    print("⚠️ participation_bot.py is deprecated. Starting main.py instead...")
    
    try:
        from main import main as new_main
        await new_main()
    except ImportError as e:
        print(f"❌ Could not import from main.py: {e}")
        print("💡 Run the bot using: python3 src/main.py")

# For backward compatibility with direct execution
if __name__ == "__main__":
    print("⚠️ This entry point is deprecated.")
    print("💡 Please use: python3 src/main.py")
    print("🔄 Attempting to start main.py...")
    
    try:
        import subprocess
        import sys
        subprocess.run([sys.executable, "src/main.py"])
    except Exception as e:
        print(f"❌ Failed to start main.py: {e}")
        sys.exit(1)