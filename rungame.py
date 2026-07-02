import asyncio
import os
from dotenv import load_dotenv
from utils.ws_client import ClawRoyaleWSClient
from utils.logger import logger

load_dotenv()

async def test_connection():
    api_key = os.getenv("BOT1_API_KEY")
    if not api_key:
        logger.error("API key is not configured in .env file.")
        return

    ws_client = ClawRoyaleWSClient(api_key=api_key)
    ws_url = "wss://cdn.clawroyale.ai/ws/join"
    
    success = await ws_client.connect(ws_url)
    if success:
        logger.info("Handshake initiation passed. Reading welcome frame...")
        welcome_frame = await ws_client.receive()
        if welcome_frame:
            logger.info("Welcome frame verified successfully.")
        await ws_client.close()
    else:
        logger.error("Failed to connect to the game server.")

if __name__ == "__main__":
    asyncio.run(test_connection())