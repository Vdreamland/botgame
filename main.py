import os
import asyncio
import sys
from config import settings
from src.websocket.lobby.join_handler import JoinHandler
from src.websocket.battle.agent_handler import AgentHandler
from src.utils.logger import logger

async def run_single_bot(bot_name: str, api_key: str):
    """Loop penanganan mandiri asinkron untuk masing-masing agen bot."""
    logger.info(f"Starting worker task for [ {bot_name} ]...")
    
    while True:
        # Menghubungkan WebSocket lobi menggunakan API Key dinamis agen
        lobby = JoinHandler(api_key=api_key)
        logger.info(f"Agent [ {bot_name} ] joining queue [ {settings.ROOM_PREFERENCE.upper()} ]...")
        
        gameplay_socket, _ = await lobby.execute_join_flow(entry_type=settings.ROOM_PREFERENCE)
        
        if not gameplay_socket:
            logger.error(f"[{bot_name}] Matchmaking failed. Retrying in 10 seconds...")
            await asyncio.sleep(10)
            continue

        logger.info(f"[OK] Agent [ {bot_name} ] entered the arena!")
        # Menghubungkan monitor pertempuran menggunakan Socket aktif dan nama agen dinamis
        battle = AgentHandler(gameplay_socket, agent_name=bot_name)
        
        # Mencatat waktu mulai koneksi monitor arena
        start_time = asyncio.get_event_loop().time()
        
        try:
            await battle.start_monitoring()
        except KeyboardInterrupt:
            logger.info(f"Manual shutdown triggered for {bot_name}.")
            break
        finally:
            try:
                await gameplay_socket.close()
            except Exception:
                pass

        # Mengalkulasi durasi aktifnya monitor
        session_duration = asyncio.get_event_loop().time() - start_time
        
        # SPAM GUARD: Jika koneksi terputus instan kurang dari 5 detik, paksa jeda 10 detik agar aman
        if session_duration < 5:
            logger.warning(f"[{bot_name}] Connection dropped prematurely. Sleeping 10 seconds to avoid spamming...")
            await asyncio.sleep(10)
            continue

        if not battle.is_alive:
            logger.info(f"[{bot_name}] Entering auto-matchmaking queue in 10 seconds...")
            await asyncio.sleep(10)

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

    # Membuat daftar tugas asinkron untuk setiap bot aktif di dalam konfigurasi
    tasks = []
    for bot in settings.BOTS:
        tasks.append(run_single_bot(bot["name"], bot["api_key"]))

    if not tasks:
        logger.error("No active bots configured in .env. Please check NUM_BOTS and BOTx_ keys.")
        return

    # Menjalankan seluruh bot secara paralel asinkron dalam satu proses aplikasi
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    if sys.platform == "win32":
        os.system("")
        
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("Bot execution stopped.")
        sys.exit(0)