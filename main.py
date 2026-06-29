import asyncio
from config import settings
from src.websocket.lobby.join_handler import JoinHandler
from src.utils.logger import logger

async def test_matchmaking_connection():
    logger.info("Checking configuration files...")
    
    # 1. Validate configuration
    try:
        settings.validate_config()
    except ValueError as e:
        logger.error(f"Failed: {str(e)}")
        logger.error("Please fix your .env file first.")
        return

    # 2. Initialize Matchmaking
    handler = JoinHandler()
    logger.info(f"Agent [ {settings.AGENT_NAME} ] joining queue [ {settings.ROOM_PREFERENCE.upper()} ]...")
    
    # Run join flow
    gameplay_socket = await handler.execute_join_flow(entry_type=settings.ROOM_PREFERENCE)
    
    if gameplay_socket:
        logger.info(f"[OK] Agent [ {settings.AGENT_NAME} ] assigned to room successfully!")
        await gameplay_socket.close()
        logger.info("[OK] Test connection closed safely.")
    else:
        logger.error(f"[FAILED] Agent [ {settings.AGENT_NAME} ] failed to allocate room [ {settings.ROOM_PREFERENCE.upper()} ].")

if __name__ == "__main__":
    # Execute loop
    asyncio.run(test_matchmaking_connection())