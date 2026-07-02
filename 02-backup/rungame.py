# rungame.py

import asyncio
from dotenv import load_dotenv

load_dotenv()

import game_data
from connection import start_multi_bots
from ui import log_system

if __name__ == "__main__":
    try:
        asyncio.run(start_multi_bots())
    except KeyboardInterrupt:
        log_system.info("Process stopped by user.")