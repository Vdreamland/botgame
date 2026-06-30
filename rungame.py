# rungame.py

import asyncio
from dotenv import load_dotenv

# Load configuration variables from .env
load_dotenv()

# Import game database to verify compile-time loading of all wiki files
import game_data
from connection import start_multi_bots
from ui import log_system

if __name__ == "__main__":
    try:
        # Start the asynchronous bot orchestrator
        asyncio.run(start_multi_bots())
    except KeyboardInterrupt:
        log_system.info("Process stopped by user.")