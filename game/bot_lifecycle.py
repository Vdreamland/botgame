import asyncio
from utils.ws_client import ClawRoyaleWSClient
from utils.api_client import ClawRoyaleAPI
from config.agen_config import auto_claim_rewards
from logs.logs_gameplay import write_gameplay_log, clear_gameplay_log
from game.lobby_coordinator import LobbyCoordinator

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
        write_gameplay_log(bot_name, f"# Turn {ws_client.last_logged_turn}", latest_view)
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

        if turn is not None and turn != ws_client.last_logged_turn and is_alive:
            write_gameplay_log(bot_name, f"# Turn {turn}", frame.get("view", {}))
            ws_client.last_logged_turn = turn

    if msg_type in ("agent_view", "turn_advanced"):
        coordinator.bots_state[bot_name]["view"] = frame.get("view", {})
        coordinator.bots_state[bot_name]["turn"] = frame.get("turn", 0)
        await coordinator.draw_table()

        self_data = frame.get("view", {}).get("self", {})
        if isinstance(self_data, dict):
            is_alive = self_data.get("isAlive")
            if is_alive is not None:
                if not is_alive:
                    if not coordinator.bots_state[bot_name].get("alive", True):
                        return False
                    coordinator.bots_state[bot_name]["alive"] = False
                    await coordinator.draw_table()
                    turn = frame.get("turn") or ws_client.last_logged_turn
                    view_data = frame.get("view", {})
                    if isinstance(view_data, dict) and "self" in view_data:
                        view_data["self"]["hp"] = 0
                        view_data["self"]["isAlive"] = False
                    write_gameplay_log(bot_name, f"# Turn {turn}", view_data)
                    write_gameplay_log(bot_name, f"[SYSTEM] Agent {bot_name} has been eliminated (HP: 0). Exiting game loop...")
                    return False
                else:
                    if not coordinator.bots_state[bot_name].get("alive", True):
                        coordinator.bots_state[bot_name]["alive"] = True
                        await coordinator.draw_table()

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
        write_gameplay_log(bot_name, f"# Turn {ws_client.last_logged_turn}", latest_view)
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
                await auto_claim_rewards(api_client, bot_name, coordinator.bots_state, coordinator.draw_table)
                is_first_run = False

            await coordinator.enter_lobby(bot_name)
            await coordinator.wait_for_lobby(bot_name)
            await coordinator.leave_lobby(bot_name)

            success = await ws_client.connect(ws_url)
            if success:
                await coordinator.enter_game(bot_name)

                try:
                    welcome_frame = await ws_client.receive()
                    if welcome_frame and welcome_frame.get("type") == "welcome":
                        decision = welcome_frame.get("decision")

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
                                    exit_msg = f"[SYSTEM] Connection timed out and REST API checks confirm Agent {bot_name} is dead. Exiting game loop..."
                                    if await _check_agent_liveness_and_cleanup(bot_name, api_client, coordinator, ws_client, exit_msg):
                                        break
                                    continue

                                if frame is None:
                                    exit_msg = "[SYSTEM] Connection closed by server. Exiting game loop..."
                                    if await _check_agent_liveness_and_cleanup(bot_name, api_client, coordinator, ws_client, exit_msg):
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
                                    print(f"[+] All Setup ready to play for {bot_name} ...")
                                elif msg_type == "error":
                                    coordinator.bots_state[bot_name]["status"] = "Disconnect"
                                    await coordinator.draw_table()
                                    break

                        elif decision == "ALREADY_IN_GAME":
                            coordinator.bots_state[bot_name]["room"] = "Room"
                            coordinator.bots_state[bot_name]["room_id"] = ""
                            coordinator.bots_state[bot_name]["status"] = "In Progress"
                            coordinator.bots_state[bot_name]["alive"] = True
                            await coordinator.draw_table()
                            print(f"[+] All Setup ready to play for {bot_name} ...")
                            while True:
                                try:
                                    frame = await asyncio.wait_for(ws_client.receive(), timeout=35.0)
                                except asyncio.TimeoutError:
                                    exit_msg = f"[SYSTEM] Connection timed out and REST API checks confirm Agent {bot_name} is dead. Exiting game loop..."
                                    if await _check_agent_liveness_and_cleanup(bot_name, api_client, coordinator, ws_client, exit_msg):
                                        break
                                    continue

                                if frame is None:
                                    exit_msg = "[SYSTEM] Connection closed by server. Exiting game loop..."
                                    if await _check_agent_liveness_and_cleanup(bot_name, api_client, coordinator, ws_client, exit_msg):
                                        break
                                
                                is_alive = await process_game_frame(frame, bot_name, coordinator, ws_client)
                                if not is_alive:
                                    break
                except Exception:
                    coordinator.bots_state[bot_name]["status"] = "Disconnect"
                    await coordinator.draw_table()
            else:
                coordinator.bots_state[bot_name]["status"] = "Disconnect"
                await coordinator.draw_table()
        except Exception as e:
            write_gameplay_log(bot_name, f"[SYSTEM] Error occurred in lifecycle: {str(e)}. Retrying in 5 seconds...")
            coordinator.bots_state[bot_name]["status"] = "Retrying"
            await coordinator.draw_table()
            await coordinator.leave_lobby(bot_name)
            await coordinator.leave_game(bot_name)
            await asyncio.sleep(5.0)
        finally:
            write_gameplay_log(bot_name, "[SYSTEM] Connection closed. Leaving game room.")
            if ws_client:
                await ws_client.close()
            await coordinator.leave_game(bot_name)

        active_count = await coordinator.get_active_count()
        if active_count > 0:
            await coordinator.wait_for_cohort(120.0)
        else:
            coordinator.bots_state[bot_name]["status"] = "Retrying"
            await coordinator.draw_table()
            await asyncio.sleep(5.0)