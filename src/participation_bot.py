#!/usr/bin/env python3
"""
Legacy participation bot entry point for backward compatibility.
This file imports and runs the new modular bot structure.
"""

import asyncio
import logging
from main import main

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Bot crashed: {e}")
        raise