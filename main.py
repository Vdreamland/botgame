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

    while True:
        lobby = JoinHandler()
        logger.info(f"Agent [ {settings.AGENT_NAME} ] joining queue [ {settings.ROOM_PREFERENCE.upper()} ]...")
        
        gameplay_socket, is_new_game = await lobby.execute_join_flow(entry_type=settings.ROOM_PREFERENCE)
        
        if not gameplay_socket:
            logger.error("[FAILED] Matchmaking failed. Retrying in 10 seconds...")
            await asyncio.sleep(10)
            continue

        if not is_new_game:
            logger.info("[REJOIN] Server redirected us back to the active game (still running).")
            try:
                await gameplay_socket.close()
            except Exception:
                pass
            logger.info("Waiting 10 seconds before attempting to request a new room...")
            await asyncio.sleep(10)
            continue

        logger.info(f"[OK] Agent [ {settings.AGENT_NAME} ] entered a NEW arena!")
        battle = AgentHandler(gameplay_socket)
        
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

        if not battle.is_alive:
            delay_seconds = 5
            logger.info(f"[TEST] Disconnecting and waiting {delay_seconds} seconds to test rejoin capability...")
            await asyncio.sleep(delay_seconds)
            
            logger.info("[TEST] Requesting a new room join flow from server now...")
            rejoin_lobby = JoinHandler()
            new_socket = await rejoin_lobby.execute_join_flow(entry_type=settings.ROOM_PREFERENCE)
            
            if new_socket:
                logger.info("[TEST_RESULT] Rejoin accepted! Activating monitor for the assigned room...")
                new_battle = AgentHandler(new_socket)
                await new_battle.start_monitoring()
                if not new_socket.open:
                    await new_socket.close()
            else:
                logger.error("[TEST_RESULT] Rejoin failed or rejected by server.")

if __name__ == "__main__":
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("Bot execution stopped.")
        sys.exit(0)