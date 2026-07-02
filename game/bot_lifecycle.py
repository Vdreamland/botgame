import asyncio
from utils.ws_client import ClawRoyaleWSClient
from utils.api_client import ClawRoyaleAPI
from config.agen_config import auto_claim_rewards
from logs.logs_gameplay import write_gameplay_log, clear_gameplay_log
from game.lobby_coordinator import LobbyCoordinator
from utils.logger import logger
from game.frame_processor import process_game_frame, get_ordinal

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

            if not in_active_game:
                if coordinator.bots_state[bot_name].get("alive", True):
                    coordinator.bots_state[bot_name]["alive"] = False
                    await coordinator.draw_table()
 
                if ws_client.last_logged_turn >= 0:
                    latest_view = coordinator.bots_state[bot_name].get("view", {})
                    if isinstance(latest_view, dict):
                        if "self" not in latest_view:
                            latest_view["self"] = {}
                        latest_view["self"]["hp"] = 0
                        latest_view["self"]["isAlive"] = False
                        death_turn = ws_client.last_logged_turn + 1
                        logger.info(f"[-] {bot_name} confirmed dead. Logging final turn {death_turn}.")
                        write_gameplay_log(bot_name, f"# Turn {death_turn}", latest_view)
                    write_gameplay_log(bot_name, "[SYSTEM] Agent has been eliminated.")
                else:
                    coordinator.bots_state[bot_name]["alive"] = True

                await coordinator.leave_game(bot_name)
                try:
                    await coordinator.enter_lobby(bot_name)
                    await coordinator.wait_for_lobby(bot_name)
                finally:
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
                                logger.warning(f"[!] {bot_name} timeout waiting for frame.")
                                break

                            if frame is None:
                                logger.warning(f"[!] {bot_name} connection closed by server.")
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
                                except Exception:
                                    room_display = str(game_id)
                                    room_id_str = str(game_id)
                                coordinator.bots_state[bot_name]["room"] = room_display[:10]
                                coordinator.bots_state[bot_name]["room_id"] = room_id_str
                                coordinator.bots_state[bot_name]["status"] = "In Progress"
                                await coordinator.draw_table()
                                logger.info(f"[+] All Setup ready to play for {bot_name} ...")
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
                        logger.info(f"[+] All Setup ready to play for {bot_name} ...")
                        while True:
                            try:
                                frame = await asyncio.wait_for(ws_client.receive(), timeout=35.0)
                            except asyncio.TimeoutError:
                                logger.warning(f"[!] {bot_name} timeout waiting for frame.")
                                break

                            if frame is None:
                                logger.warning(f"[!] {bot_name} connection closed by server.")
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
            await asyncio.sleep(5.0)
        finally:
            if ws_client:
                await ws_client.close()

        active_count = await coordinator.get_active_count(bot_name)
        is_bot_alive = coordinator.bots_state[bot_name].get("alive", True)
        if active_count > 0 and not is_bot_alive:
            await coordinator.wait_for_cohort(bot_name, 120.0)
        elif not is_bot_alive:
            coordinator.bots_state[bot_name]["status"] = "Retrying"
            await coordinator.draw_table()
            await asyncio.sleep(5.0)