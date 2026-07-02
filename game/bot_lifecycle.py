import asyncio
from utils.ws_client import ClawRoyaleWSClient
from utils.api_client import ClawRoyaleAPI
from config.agen_config import auto_claim_rewards
from logs.logs_gameplay import write_gameplay_log
from game.lobby_coordinator import LobbyCoordinator

def get_ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

async def process_game_frame(frame: dict, bot_name: str, coordinator: LobbyCoordinator, ws_client) -> bool:
    if not isinstance(frame, dict):
        return True

    msg_type = frame.get("type")
    if msg_type in ("agent_view", "turn_advanced"):
        coordinator.bots_state[bot_name]["view"] = frame.get("view", {})
        await coordinator.draw_table()

    self_data = frame.get("view", {}).get("self", {})
    if isinstance(self_data, dict):
        is_alive = self_data.get("isAlive")
        if is_alive is not None:
            if coordinator.bots_state[bot_name]["alive"] != is_alive:
                coordinator.bots_state[bot_name]["alive"] = is_alive
                await coordinator.draw_table()
            if not is_alive:
                turn = frame.get("turn") or ws_client.last_logged_turn
                view_data = frame.get("view", {})
                if isinstance(view_data, dict) and "self" in view_data:
                    view_data["self"]["hp"] = 0
                    view_data["self"]["isAlive"] = False
                write_gameplay_log(bot_name, f"# Turn {turn}", view_data)
                return False

            if frame.get("type") == "game_ended":
                coordinator.bots_state[bot_name]["alive"] = False
                await coordinator.draw_table()
                latest_view = coordinator.bots_state[bot_name].get("view", {})
                if isinstance(latest_view, dict):
                    if "self" not in latest_view:
                        latest_view["self"] = {}
                    latest_view["self"]["hp"] = 0
                    latest_view["self"]["isAlive"] = False
                write_gameplay_log(bot_name, f"# Turn {ws_client.last_logged_turn}", latest_view)
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
    ws_client = ClawRoyaleWSClient(api_key=api_key, bot_name=bot_name)
    ws_url = "wss://cdn.clawroyale.ai/ws/join"

    while True:
        clear_gameplay_log(bot_name)

        await auto_claim_rewards(api_client, bot_name, coordinator.bots_state, coordinator.draw_table)

        await coordinator.enter_lobby(bot_name)

        is_ready = await coordinator.wait_for_lobby(bot_name, 15.0)
        if not is_ready:
            await coordinator.leave_lobby(bot_name)
            await asyncio.sleep(2.0)
            continue

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
                                coordinator.bots_state[bot_name]["alive"] = False
                                await coordinator.draw_table()
                                latest_view = coordinator.bots_state[bot_name].get("view", {})
                                if isinstance(latest_view, dict):
                                    if "self" not in latest_view:
                                        latest_view["self"] = {}
                                    latest_view["self"]["hp"] = 0
                                    latest_view["self"]["isAlive"] = False
                                write_gameplay_log(bot_name, f"# Turn {ws_client.last_logged_turn}", latest_view)
                                break
                            continue

                        if frame is None:
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
                                coordinator.bots_state[bot_name]["alive"] = False
                                await coordinator.draw_table()
                                latest_view = coordinator.bots_state[bot_name].get("view", {})
                                if isinstance(latest_view, dict):
                                    if "self" not in latest_view:
                                        latest_view["self"] = {}
                                    latest_view["self"]["hp"] = 0
                                    latest_view["self"]["isAlive"] = False
                                write_gameplay_log(bot_name, f"# Turn {ws_client.last_logged_turn}", latest_view)
                                break
                            continue

                        if frame is None:
                            break
                        
                        is_alive = await process_game_frame(frame, bot_name, coordinator, ws_client)
                        if not is_alive:
                            break
                else:
                    coordinator.bots_state[bot_name]["status"] = "Disconnect"
                    await coordinator.draw_table()
        except Exception:
            coordinator.bots_state[bot_name]["status"] = "Disconnect"
            await coordinator.draw_table()
        finally:
            await ws_client.close()
            await coordinator.leave_game(bot_name)

        active_count = await coordinator.get_active_count()
        if active_count > 0:
            await coordinator.wait_for_cohort(120.0)
        else:
            coordinator.bots_state[bot_name]["status"] = "Retrying"
            await coordinator.draw_table()
        await asyncio.sleep(5.0)