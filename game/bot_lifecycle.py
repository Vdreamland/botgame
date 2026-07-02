import asyncio
from utils.ws_client import ClawRoyaleWSClient
from utils.api_client import ClawRoyaleAPI
from config.agen_config import auto_claim_rewards
from logs.logs_gameplay import write_gameplay_log, clear_gameplay_log
from game.lobby_coordinator import LobbyCoordinator
from utils.logger import logger

def get_ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

async def _check_agent_liveness_and_cleanup(
    bot_name: str,
    api_client: ClawRoyaleAPI,
    coordinator: LobbyCoordinator,
    ws_client,
    exit_msg: str
) -> bool:
    logger.info(f"[*] {bot_name} connection lost/ended. Checking liveness via REST API...")
    profile_res = await api_client.get_my_profile()
    is_still_alive = False
    if profile_res.get("success"):
        data = profile_res.get("data", {})
        current_games = data.get("currentGames", [])
        for g in current_games:
            if g.get("gameId") == coordinator.bots_state[bot_name].get("room_id") or g.get("isAlive") is True:
                if g.get("isAlive") is True:
                    is_still_alive = True
                    break
    logger.info(f"[*] {bot_name} liveness status: is_still_alive={is_still_alive}")
    if not is_still_alive:
        if coordinator.bots_state[bot_name]["alive"]:
            coordinator.bots_state[bot_name]["alive"] = False
            await coordinator.draw_table()
        latest_view = coordinator.bots_state[bot_name].get("view", {})
        if isinstance(latest_view, dict):
            if "self" not in latest_view:
                latest_view["self"] = {}
            latest_view["self"]["hp"] = 0
            latest_view["self"]["isAlive"] = False
        death_turn = ws_client.last_logged_turn + 1 if ws_client.last_logged_turn >= 0 else 1
        logger.info(f"[-] {bot_name} eliminated. Writing final turn {death_turn} to log.")
        write_gameplay_log(bot_name, f"# Turn {death_turn}", latest_view)
        write_gameplay_log(bot_name, exit_msg)
        return True
    return False

async def process_game_frame(frame: dict, bot_name: str, coordinator: LobbyCoordinator, ws_client) -> bool:
    if not isinstance(frame, dict):
        return True

    msg_type = frame.get("type")
    
    if msg_type in ("agent_view", "turn_advanced"):
        turn = frame.get("turn")
        self_data = frame.get("view", {}).get("self", {})
        is_alive = True
        if isinstance(self_data, dict):
            is_alive = self_data.get("isAlive", True)
            if self_data.get("hp") == 0:
                is_alive = False

        if turn is not None and turn != ws_client.last_logged_turn and is_alive:
            write_gameplay_log(bot_name, f"# Turn {turn}", frame.get("view", {}))
            ws_client.last_logged_turn = turn

    if msg_type in ("agent_view", "turn_advanced"):
        coordinator.bots_state[bot_name]["view"] = frame.get("view", {})
        coordinator.bots_state[bot_name]["turn"] = frame.get("turn", 0)
        await coordinator.draw_table()

        view_data = frame.get("view", {})
        self_data = view_data.get("self")
        
        if self_data is None:
            logger.info(f"[*] {bot_name} self-data missing from view. Verifying status...")
            from utils.api_client import ClawRoyaleAPI
            api_client = ClawRoyaleAPI(api_key=ws_client.api_key)
            is_dead = await _check_agent_liveness_and_cleanup(
                bot_name, api_client, coordinator, ws_client,
                f"[SYSTEM] Agent {bot_name} is dead (self-data missing)."
            )
            if is_dead:
                return False
        elif isinstance(self_data, dict):
            is_alive = self_data.get("isAlive")
            hp = self_data.get("hp", 100)
            if is_alive is False or hp == 0:
                if not coordinator.bots_state[bot_name].get("alive", True):
                    return False
                coordinator.bots_state[bot_name]["alive"] = False
                await coordinator.draw_table()
                turn = frame.get("turn") or ws_client.last_logged_turn
                logger.info(f"[-] {bot_name} has been eliminated (HP: 0). Logging turn {turn}.")
                if "self" in view_data:
                    view_data["self"]["hp"] = 0
                    view_data["self"]["isAlive"] = False
                write_gameplay_log(bot_name, f"# Turn {turn}", view_data)
                write_gameplay_log(bot_name, f"[SYSTEM] Agent {bot_name} has been eliminated (HP: 0). Exiting game loop...")
                return False
            else:
                if not coordinator.bots_state[bot_name].get("alive", True):
                    coordinator.bots_state[bot_name]["alive"] = True
                    await coordinator.draw_table()

    if msg_type == "event":
        event_name = frame.get("event")
        event_data = frame.get("data", {})
        my_agent_id = coordinator.bots_state[bot_name].get("agent_id")
        if event_name == "agent_died" and event_data.get("agentId") == my_agent_id:
            logger.info(f"[-] {bot_name} received agent_died event. Logging turn.")
            coordinator.bots_state[bot_name]["alive"] = False
            await coordinator.draw_table()
            latest_view = coordinator.bots_state[bot_name].get("view", {})
            if isinstance(latest_view, dict):
                if "self" not in latest_view:
                    latest_view["self"] = {}
                latest_view["self"]["hp"] = 0
                latest_view["self"]["isAlive"] = False
            turn = frame.get("turn") or ws_client.last_logged_turn
            write_gameplay_log(bot_name, f"# Turn {turn}", latest_view)
            write_gameplay_log(bot_name, f"[SYSTEM] Agent {bot_name} received agent_died event (HP: 0). Exiting game loop...")
            return False

    if msg_type == "game_ended":
        if not coordinator.bots_state[bot_name].get("alive", True):
            return False
        coordinator.bots_state[bot_name]["alive"] = False
        await coordinator.draw_table()
        latest_view = coordinator.bots_state[bot_name].get("view", {})
        if isinstance(latest_view, dict):
            if "self" not in latest_view:
                latest_view["self"] = {}
            latest_view["self"]["hp"] = 0
            latest_view["self"]["isAlive"] = False
        death_turn = ws_client.last_logged_turn + 1 if ws_client.last_logged_turn >= 0 else 1
        logger.info(f"[-] {bot_name} match ended (game_ended received). Logging final turn {death_turn}.")
        write_gameplay_log(bot_name, f"# Turn {death_turn}", latest_view)
        write_gameplay_log(bot_name, "[SYSTEM] Match has ended (game_ended received). Exiting game loop...")
        return False

    game_id = frame.get("gameId") or frame.get("matchId")
    if game_id:
        try:
            m_id = int(game_id)
            room_display = get_ordinal(m_id)
            room_id_str = str(game_id)
        except ValueError:
            room_display = str(game_id)
            room_id_str = str(game_id)
        if coordinator.bots_state[bot_name]["room"] != room_display[:10]:
            coordinator.bots_state[bot_name]["room"] = room_display[:10]
            coordinator.bots_state[bot_name]["room_id"] = room_id_str
            await coordinator.draw_table()
    
    return True

async def run_bot_lifecycle(bot_info: dict, coordinator: LobbyCoordinator, room_preference: str):
    bot_name = bot_info["name"]
    api_key = bot_info["api_key"]

    api_client = ClawRoyaleAPI(api_key=api_key)
    ws_url = "wss://cdn.clawroyale.ai/ws/join"
    is_first_run = True

    while True:
        ws_client = None
        try:
            clear_gameplay_log(bot_name)
            ws_client = ClawRoyaleWSClient(api_key=api_key, bot_name=bot_name)

            if is_first_run:
                logger.info(f"[*] {bot_name} claiming first-run rewards...")
                await auto_claim_rewards(api_client, bot_name, coordinator.bots_state, coordinator.draw_table)
                is_first_run = False

            logger.info(f"[*] {bot_name} checking ongoing game profile...")
            profile_res = await api_client.get_my_profile()
            in_active_game = False
            if profile_res.get("success"):
                data = profile_res.get("data", {})
                current_games = data.get("currentGames", [])
                for g in current_games:
                    if g.get("isAlive") is True:
                        in_active_game = True
                        coordinator.bots_state[bot_name]["agent_id"] = g.get("agentId")
                        coordinator.bots_state[bot_name]["room_id"] = g.get("gameId")
                        break

            bypass_lobby = getattr(coordinator, "bypass_lobby_on_startup", False)
            if not in_active_game and not (is_first_run and bypass_lobby):
                logger.info(f"[*] {bot_name} entering lobby coordinator...")
                await coordinator.enter_lobby(bot_name)
                logger.info(f"[*] {bot_name} waiting in lobby for cohort...")
                await coordinator.wait_for_lobby(bot_name)
                logger.info(f"[*] {bot_name} lobby is full, leaving lobby and connecting...")
                await coordinator.leave_lobby(bot_name)
            else:
                if in_active_game:
                    logger.info(f"[*] {bot_name} detected active game, bypassing lobby...")
                else:
                    logger.info(f"[*] {bot_name} bypassing lobby due to other active game on startup...")

            logger.info(f"[*] {bot_name} connecting to WebSocket: {ws_url}")
            success = await ws_client.connect(ws_url)
            if success:
                logger.info(f"[+] {bot_name} WebSocket connected. Entering game...")
                await coordinator.enter_game(bot_name)

                try:
                    welcome_frame = await ws_client.receive()
                    if welcome_frame and welcome_frame.get("type") == "welcome":
                        decision = welcome_frame.get("decision")
                        logger.info(f"[*] {bot_name} welcome received. Decision: {decision}")

                        if decision in ("ASK_ENTRY_TYPE", "FREE_ONLY"):
                            hello_payload = {
                                "type": "hello",
                                "entryType": room_preference,
                                "version": ws_client.api_version
                            }
                            await ws_client.send(hello_payload)

                            while True:
                                try:
                                    frame = await asyncio.wait_for(ws_client.receive(), timeout=35.0)
                                except asyncio.TimeoutError:
                                    logger.warning(f"[!] {bot_name} timeout waiting for frame.")
                                    exit_msg = f"[SYSTEM] Connection timed out and REST API checks confirm Agent {bot_name} is dead. Exiting game loop..."
                                    await _check_agent_liveness_and_cleanup(bot_name, api_client, coordinator, ws_client, exit_msg)
                                    break

                                if frame is None:
                                    logger.warning(f"[!] {bot_name} connection closed by server.")
                                    exit_msg = "[SYSTEM] Connection closed by server. Exiting game loop..."
                                    await _check_agent_liveness_and_cleanup(bot_name, api_client, coordinator, ws_client, exit_msg)
                                    break

                                is_alive = await process_game_frame(frame, bot_name, coordinator, ws_client)
                                if not is_alive:
                                    break

                                msg_type = frame.get("type") if isinstance(frame, dict) else None
                                if msg_type == "queued":
                                    coordinator.bots_state[bot_name]["room"] = "Queue"
                                    coordinator.bots_state[bot_name]["room_id"] = ""
                                    coordinator.bots_state[bot_name]["status"] = "Queued"
                                    await coordinator.draw_table()
                                elif msg_type in ("assigned", "joined"):
                                    game_id = frame.get("gameId") or frame.get("matchId") or "Room"
                                    agent_id = frame.get("agentId")
                                    if agent_id:
                                        coordinator.bots_state[bot_name]["agent_id"] = agent_id
                                    try:
                                        m_id = int(game_id)
                                        room_display = get_ordinal(m_id)
                                        room_id_str = str(game_id)
                                    except ValueError:
                                        room_display = str(game_id)
                                        room_id_str = str(game_id)
                                    coordinator.bots_state[bot_name]["room"] = room_display[:10]
                                    coordinator.bots_state[bot_name]["room_id"] = room_id_str
                                    coordinator.bots_state[bot_name]["status"] = "In Progress"
                                    await coordinator.draw_table()
                                    logger.info(f"[+] All Setup ready to play for {bot_name} ...")
                                elif msg_type == "error":
                                    logger.error(f"[!] {bot_name} received error frame.")
                                    coordinator.bots_state[bot_name]["status"] = "Disconnect"
                                    await coordinator.draw_table()
                                    break

                        elif decision == "ALREADY_IN_GAME":
                            coordinator.bots_state[bot_name]["room"] = "Room"
                            coordinator.bots_state[bot_name]["room_id"] = ""
                            coordinator.bots_state[bot_name]["status"] = "In Progress"
                            coordinator.bots_state[bot_name]["alive"] = True
                            await coordinator.draw_table()
                            logger.info(f"[+] All Setup ready to play for {bot_name} ...")
                            while True:
                                try:
                                    frame = await asyncio.wait_for(ws_client.receive(), timeout=35.0)
                                except asyncio.TimeoutError:
                                    logger.warning(f"[!] {bot_name} timeout waiting for frame.")
                                    exit_msg = f"[SYSTEM] Connection timed out and REST API checks confirm Agent {bot_name} is dead. Exiting game loop..."
                                    await _check_agent_liveness_and_cleanup(bot_name, api_client, coordinator, ws_client, exit_msg)
                                    break

                                if frame is None:
                                    logger.warning(f"[!] {bot_name} connection closed by server.")
                                    exit_msg = "[SYSTEM] Connection closed by server. Exiting game loop..."
                                    await _check_agent_liveness_and_cleanup(bot_name, api_client, coordinator, ws_client, exit_msg)
                                    break
                                
                                is_alive = await process_game_frame(frame, bot_name, coordinator, ws_client)
                                if not is_alive:
                                    break
                except Exception as inner_e:
                    logger.error(f"[!] {bot_name} error in inner game loop: {str(inner_e)}")
                    coordinator.bots_state[bot_name]["status"] = "Disconnect"
                    await coordinator.draw_table()
            else:
                logger.error(f"[!] {bot_name} failed to connect to WebSocket.")
                coordinator.bots_state[bot_name]["status"] = "Disconnect"
                await coordinator.draw_table()
        except Exception as e:
            logger.error(f"[!] {bot_name} error in outer loop: {str(e)}")
            write_gameplay_log(bot_name, f"[SYSTEM] Error occurred in lifecycle: {str(e)}. Retrying in 5 seconds...")
            coordinator.bots_state[bot_name]["status"] = "Retrying"
            await coordinator.draw_table()
            await coordinator.leave_lobby(bot_name)
            await coordinator.leave_game(bot_name)
            await asyncio.sleep(5.0)
        finally:
            logger.info(f"[-] {bot_name} leaving game session.")
            write_gameplay_log(bot_name, "[SYSTEM] Connection closed. Leaving game room.")
            if ws_client:
                await ws_client.close()
            await coordinator.leave_game(bot_name)

        active_count = await coordinator.get_active_count(bot_name)
        is_bot_alive = coordinator.bots_state[bot_name].get("alive", True)
        if active_count > 0 and not is_bot_alive:
            logger.info(f"[*] {bot_name} waiting for other active cohort bots to finish...")
            await coordinator.wait_for_cohort(bot_name, 120.0)
        elif not is_bot_alive:
            logger.info(f"[*] {bot_name} retrying loop in 5 seconds...")
            coordinator.bots_state[bot_name]["status"] = "Retrying"
            await coordinator.draw_table()
            await asyncio.sleep(5.0)