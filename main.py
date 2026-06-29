import os
import asyncio
import sys
from config import settings
from src.websocket.lobby.join_handler import JoinHandler
from src.websocket.battle.agent_handler import AgentHandler
from src.utils.logger import logger

async def start_bot():
    logger.info("Checking configuration files...")
    try:
        settings.validate_config()
    except ValueError as e:
        logger.error(f"\033[91mFailed: {str(e)}\033[0m")
        return

    try:
        from config import game_data
        logger.info("\033[92mGame database assets loaded successfully.\033[0m")
    except Exception as e:
        logger.error(f"\033[91mFailed to load game database assets: {str(e)}\033[0m")
        return

    # Loop utama asinkron abadi penanganan antrean & pengaman spamming
    while True:
        lobby = JoinHandler()
        logger.info(f"Agent [ {settings.AGENT_NAME} ] joining queue [ {settings.ROOM_PREFERENCE.upper()} ]...")
        
        gameplay_socket, _ = await lobby.execute_join_flow(entry_type=settings.ROOM_PREFERENCE)
        
        if not gameplay_socket:
            logger.error("[FAILED] Matchmaking failed. Retrying in 10 seconds...")
            await asyncio.sleep(10)
            continue

        logger.info(f"[OK] Agent [ {settings.AGENT_NAME} ] entered the arena!")
        battle = AgentHandler(gameplay_socket)
        
        # Mencatat waktu mulai koneksi monitor arena
        start_time = asyncio.get_event_loop().time()
        
        try:
            await battle.start_monitoring()
        except KeyboardInterrupt:
            logger.info("Manual shutdown triggered.")
            break
        finally:
            try:
                await gameplay_socket.close()
            except Exception:
                pass

        # Mengalkulasi durasi aktifnya monitor
        session_duration = asyncio.get_event_loop().time() - start_time
        
        # SPAM GUARD: Jika koneksi terputus instan kurang dari 5 detik, paksa jeda 10 detik agar aman dari rate-limit
        if session_duration < 5:
            logger.warning("[WARNING] Connection dropped prematurely. Sleeping 10 seconds to avoid spamming...")
            await asyncio.sleep(10)
            continue

        if not battle.is_alive:
            logger.info("[DEATH] Entering auto-matchmaking queue in 10 seconds...")
            await asyncio.sleep(10)

if __name__ == "__main__":
    if sys.platform == "win32":
        os.system("")
        
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("Bot execution stopped.")
        sys.exit(0)