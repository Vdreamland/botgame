import asyncio
from logs.logs_gameplay import write_gameplay_log
from ai.Strategy import make_decision
from utils.logger import logger
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
 
    if isinstance(self_data, dict):
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
        if event_name == "agent_died":
            if event_data.get("agentId") == my_agent_id:
                logger.info(f"[-] {bot_name} received agent_died event.")
                coordinator.bots_state[bot_name]["alive"] = False
                await coordinator.draw_table()
                latest_view = coordinator.bots_state[bot_name].get("view", {})
                if isinstance(latest_view, dict):
                    if "self" not in latest_view:
                        latest_view["self"] = {}
                    latest_view["self"]["hp"] = 0
                    latest_view["self"]["isAlive"] = False
                turn = frame.get("turn") or ws_client.last_logged_turn
                if turn >= 0:
                    write_gameplay_log(bot_name, f"# Turn {turn}", latest_view)
                write_gameplay_log(bot_name, f"[SYSTEM] Agent {bot_name} received agent_died event (HP: 0). Exiting game loop...")
                return False
            else:
                death_region = event_data.get("regionId") or event_data.get("region_id") or event_data.get("region")
                if death_region:
                    from ai.Strategy.memory import mark_death_spot
                    mark_death_spot(death_region)

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
 
        if ws_client.last_logged_turn >= 0:
            death_turn = ws_client.last_logged_turn + 1
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
 
    if msg_type == "action_result":
        success = frame.get("success", True)
        if not success:
            err = frame.get("error", {})
            logger.warning(f"[!] Action result warning: {err.get('message', 'Unknown')} (Code: {err.get('code', 'None')})")

    if msg_type == "agent_view":
        current_region = frame.get("view", {}).get("currentRegion", {})
        curr_id = current_region.get("id") if isinstance(current_region, dict) else None
        if curr_id:
            from ai.Strategy.memory import mark_visited
            mark_visited(curr_id)

        self_data = frame.get("view", {}).get("self", {})
        is_agent_alive = True
        can_act = True
        if isinstance(self_data, dict):
            is_agent_alive = self_data.get("isAlive", True)
            can_act = self_data.get("canAct", True)
        if self_data.get("hp") == 0:
            is_agent_alive = False

        if is_agent_alive and can_act:
            action_payload = make_decision(frame.get("view", {}), bot_name)
            act_type = action_payload.get("type", "unknown")
            act_name = action_payload.get("name", "None")
            act_score = action_payload.get("score", 0.0)
            act_report = action_payload.get("strategy_report", "None")
            logger.info(f"[»] {bot_name} executes action: {act_type} -> {act_name} (Score: {act_score:.2f})")
            logger.info(f"[~] {bot_name} strategic plan: {act_report}")
            clean_payload = {k: v for k, v in action_payload.items() if k not in ("name", "score", "strategy_report")}
            wrapped_payload = {
                "type": "action",
                "data": clean_payload
            }
            await ws_client.send(wrapped_payload)

    if msg_type == "can_act_changed" and frame.get("canAct") is True:
        stored_view = coordinator.bots_state[bot_name].get("view", {})
        if stored_view:
            self_data = stored_view.get("self", {})
            is_agent_alive = True
            if isinstance(self_data, dict):
                is_agent_alive = self_data.get("isAlive", True)
                stored_view["self"]["canAct"] = True
            if self_data.get("hp") == 0:
                is_agent_alive = False

            if is_agent_alive:
                action_payload = make_decision(stored_view, bot_name)
                act_type = action_payload.get("type", "unknown")
                act_name = action_payload.get("name", "None")
                act_score = action_payload.get("score", 0.0)
                act_report = action_payload.get("strategy_report", "None")
                logger.info(f"[»] {bot_name} executes action: {act_type} -> {act_name} (Score: {act_score:.2f})")
                logger.info(f"[~] {bot_name} strategic plan: {act_report}")
                clean_payload = {k: v for k, v in action_payload.items() if k not in ("name", "score", "strategy_report")}
                wrapped_payload = {
                    "type": "action",
                    "data": clean_payload
                }
                await ws_client.send(wrapped_payload)

    return True