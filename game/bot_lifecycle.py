import asyncio
import aiohttp
import json
from utils.logger import logger
from utils.ws_client import ClawRoyaleWSClient
from utils.api_client import ClawRoyaleAPI
from config.agen_config import get_configured_bots, get_room_preference
from game.lobby_coordinator import LobbyCoordinator
from game.frame_processor import process_game_frame
from logs.logs_gameplay import write_gameplay_log, clear_gameplay_log
from logs.quest_reward_log import log_redeem_attempt, log_redeem_success, log_redeem_failed

async def run_bot_lifecycle(bot_config: dict, coordinator: LobbyCoordinator, room_preference: str = None) -> None:
    bot_name = bot_config.get("name")
    api_key = bot_config.get("api_key")
    if not api_key:
        return

    api = ClawRoyaleAPI(api_key)
    ws_client = ClawRoyaleWSClient(bot_name)

    bypass_lobby_on_startup = True

    while True:
        try:
            profile = await api.get_my_profile()
            if not profile:
                logger.error(f"[ERROR] Could not fetch profile for {bot_name}.")
                await asyncio.sleep(5)
                continue

            current_games = profile.get("currentGames", {})
            active_game_id = None
            if isinstance(current_games, dict):
                for g_id, g_status in current_games.items():
                    if isinstance(g_status, dict) and g_status.get("status") == "active":
                        active_game_id = g_id
                        break

            if active_game_id:
                agent_id = None
                members = current_games[active_game_id].get("members", {})
                if isinstance(members, dict):
                    for a_id, details in members.items():
                        if isinstance(details, dict) and details.get("name") == bot_name:
                            agent_id = a_id
                            break
                coordinator.bots_state[bot_name]["agent_id"] = agent_id
                coordinator.bots_state[bot_name]["game_id"] = active_game_id
                coordinator.bots_state[bot_name]["alive"] = True
                
                ws_url = "wss://cdn.clawroyale.ai/ws/agent"
                logger.info(f"[*] {bot_name} reconnecting directly to active game WebSocket -> {ws_url}")
                connected = await ws_client.connect(ws_url, api_key)
                if connected:
                    logger.info(f"[+] {bot_name} reconnected directly to active game.")
                    game_ended_normally = False
                    while True:
                        msg = await ws_client.receive()
                        if msg is None:
                            logger.warning(f"[-] {bot_name} disconnected from game WebSocket.")
                            break
                        
                        try:
                            frame = json.loads(msg)
                        except json.JSONDecodeError:
                            continue
                        
                        success = await process_game_frame(frame, bot_name, coordinator, ws_client)
                        if not success:
                            game_ended_normally = True
                            break
                    await ws_client.close()
                    if game_ended_normally:
                        await coordinator.leave_game(bot_name)
                await asyncio.sleep(5)
                continue

            if coordinator.bots_state[bot_name].get("alive", False):
                coordinator.bots_state[bot_name]["alive"] = False
                latest_view = coordinator.bots_state[bot_name].get("view", {})
                if isinstance(latest_view, dict):
                    if "self" not in latest_view:
                        latest_view["self"] = {}
                    latest_view["self"]["hp"] = 0
                    latest_view["self"]["isAlive"] = False
                last_turn = coordinator.bots_state[bot_name].get("turn", 0) or ws_client.last_logged_turn
                death_turn = last_turn + 1 if last_turn else 1
                logger.info(f"[-] {bot_name} has been eliminated (detected from profile status). Logging final turn {death_turn}.")
                write_gameplay_log(bot_name, f"# Turn {death_turn}", latest_view)
                write_gameplay_log(bot_name, f"[SYSTEM] Agent {bot_name} was eliminated during connection loss (HP: 0).")
                await coordinator.leave_game(bot_name)

            bypass = bypass_lobby_on_startup
            bypass_lobby_on_startup = False

            await coordinator.enter_lobby(bot_name)
            await coordinator.wait_for_lobby(bot_name, bypass_lobby=bypass)

            ws_url = "wss://cdn.clawroyale.ai/ws/join"
            logger.info(f"[*] {bot_name} connecting to WebSocket -> {ws_url}")
            
            connected = await ws_client.connect(ws_url, api_key)
            if not connected:
                logger.error(f"[ERROR] Could not connect to WebSocket for {bot_name}.")
                await coordinator.leave_lobby(bot_name)
                await asyncio.sleep(5)
                continue

            ws_client.last_acted_turn = -1
            ws_client.last_logged_turn = -1

            while True:
                msg = await ws_client.receive()
                if msg is None:
                    logger.warning(f"[-] {bot_name} WebSocket connection closed.")
                    break
                
                try:
                    frame = json.loads(msg)
                except json.JSONDecodeError:
                    continue
                
                f_type = frame.get("type")
                if f_type == "welcome":
                    dec = frame.get("decision")
                    if dec == "ALREADY_IN_GAME":
                        logger.info(f"[+] All Setup ready to play for {bot_name} ...")
                        coordinator.bots_state[bot_name]["alive"] = True
                        await coordinator.enter_game(bot_name)
                        break
                    elif dec == "ASK_ENTRY_TYPE":
                        hello_payload = {
                            "type": "hello",
                            "room_preference": room_preference or get_room_preference(),
                            "relics": [],
                            "packs": []
                        }
                        await ws_client.send(hello_payload)
                        continue
                
                if f_type == "assigned":
                    data = frame.get("data", {})
                    coordinator.bots_state[bot_name]["agent_id"] = data.get("agentId")
                    coordinator.bots_state[bot_name]["game_id"] = data.get("gameId")
                    coordinator.bots_state[bot_name]["alive"] = True
                    await coordinator.enter_game(bot_name)
                    logger.info(f"[+] All Setup ready to play for {bot_name} ...")
                    break

            await ws_client.close()

            if coordinator.bots_state[bot_name].get("alive", False):
                ws_url = "wss://cdn.clawroyale.ai/ws/agent"
                connected = await ws_client.connect(ws_url, api_key)
                if connected:
                    game_ended_normally = False
                    while True:
                        msg = await ws_client.receive()
                        if msg is None:
                            logger.warning(f"[-] {bot_name} disconnected from game WebSocket.")
                            break
                        
                        try:
                            frame = json.loads(msg)
                        except json.JSONDecodeError:
                            continue
                        
                        success = await process_game_frame(frame, bot_name, coordinator, ws_client)
                        if not success:
                            game_ended_normally = True
                            break
                    await ws_client.close()
                    if game_ended_normally:
                        await coordinator.leave_game(bot_name)

        except Exception as e:
            logger.error(f"[ERROR] Error in {bot_name} game execution loop: {e}")
            await asyncio.sleep(5)