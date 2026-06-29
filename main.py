import os
import asyncio
import sys
from config import settings
from src.websocket.lobby.join_handler import JoinHandler
from src.websocket.battle.agent_handler import AgentHandler
from src.utils.logger import logger

async def run_single_bot(bot_name: str, api_key: str):
    """Asynchronous self-contained worker loop for each individual bot."""
    logger.info(f"Starting worker task for [ {bot_name} ]...")
    
    while True:
        # SYNC BARRIER: Wait until all allied bots are fully out of any matches
        while any(settings.ACTIVE_BOTS_IN_GAME.values()):
            await asyncio.sleep(1)
        
        # Flush shared databases to ensure clean slate for the upcoming new match
        settings.SHARED_LOOT_TARGETS.clear()
        settings.SOS_TARGETS.clear()
        settings.SHARED_VISITED_HISTORY.clear()
        
        lobby = JoinHandler(api_key=api_key)
        logger.info(f"Agent [ {bot_name} ] joining queue [ {settings.ROOM_PREFERENCE.upper()} ]...")
        
        gameplay_socket, _ = await lobby.execute_join_flow(entry_type=settings.ROOM_PREFERENCE)
        
        if not gameplay_socket:
            logger.error(f"[{bot_name}] Matchmaking failed. Retrying in 10 seconds...")
            await asyncio.sleep(10)
            continue

        logger.info(f"[OK] Agent [ {bot_name} ] entered the arena!")
        
        # Mark this bot as actively playing
        settings.ACTIVE_BOTS_IN_GAME[bot_name] = True
        
        battle = AgentHandler(gameplay_socket, agent_name=bot_name)
        start_time = asyncio.get_event_loop().time()
        
        try:
            await battle.start_monitoring()
        except KeyboardInterrupt:
            logger.info(f"Manual shutdown triggered for {bot_name}.")
            break
        except Exception as e:
            logger.error(f"[{bot_name}] Error during monitoring: {str(e)}")
        finally:
            # Mark this bot as inactive immediately upon match termination/death
            settings.ACTIVE_BOTS_IN_GAME[bot_name] = False
            try:
                await gameplay_socket.close()
            except Exception:
                pass

        session_duration = asyncio.get_event_loop().time() - start_time
        if session_duration < 5:
            logger.warning(f"[{bot_name}] Connection dropped prematurely. Sleeping 10 seconds...")
            await asyncio.sleep(10)
            continue

        if not battle.is_alive:
            logger.info(f"[{bot_name}] Waiting for other squad members to finish...")
            # Loop restarts, but barrier will block entering queue until the remaining bot dies/ends

async def start_bot():
    """Validates configuration and launches parallel asynchronous bot tasks."""
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

    # Create asynchronous tasks for all configured active bots
    tasks = []
    for bot in settings.BOTS:
        tasks.append(run_single_bot(bot["name"], bot["api_key"]))

    if not tasks:
        logger.error("No active bots configured in .env. Please check NUM_BOTS and BOTx_ keys.")
        return

    # Launch all bots concurrently under a single execution process
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    if sys.platform == "win32":
        os.system("")
        
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("Bot execution stopped.")
        sys.exit(0)