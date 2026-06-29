import asyncio
import sys
from config import settings
from src.websocket.lobby.join_handler import JoinHandler
from src.websocket.battle.agent_handler import AgentHandler
from src.utils.logger import logger

async def start_bot():
    logger.info("Checking configuration files...")
    
    # 1. Validate configuration
    try:
        settings.validate_config()
    except ValueError as e:
        logger.error(f"Failed: {str(e)}")
        logger.error("Please fix your .env file first.")
        return

    # 2. Matchmaking Process
    lobby = JoinHandler()
    logger.info(f"Agent [ {settings.AGENT_NAME} ] joining queue [ {settings.ROOM_PREFERENCE.upper()} ]...")
    
    gameplay_socket = await lobby.execute_join_flow(entry_type=settings.ROOM_PREFERENCE)
    
    if not gameplay_socket:
        logger.error(f"[FAILED] Agent [ {settings.AGENT_NAME} ] failed to allocate room.")
        return

    # 3. Battle Monitoring Process
    logger.info(f"[OK] Agent [ {settings.AGENT_NAME} ] entered the arena!")
    battle = AgentHandler(gameplay_socket)
    
    try:
        # Menjalankan monitor hingga game selesai atau Ctrl + C ditekan
        await battle.start_monitoring()
    except KeyboardInterrupt:
        logger.info("Manual shutdown triggered by user (Ctrl+C).")
    finally:
        # Menutup socket dengan aman saat keluar
        if not gameplay_socket.closed:
            await gameplay_socket.close()
            logger.info("[OK] Battle connection closed safely.")

if __name__ == "__main__":
    try:
        # Menjalankan loop utama asinkron
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        # Penanganan jika Ctrl + C ditekan saat inisialisasi
        logger.info("Bot execution stopped.")
        sys.exit(0)