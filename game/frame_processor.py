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

def get_weapon_atk(w_name: str) -> int:
    from game_data.weapon_info import WEAPONS
    return WEAPONS.get(w_name, {}).get("atk_bonus", 0)

async def _execute_decision(view: dict, bot_name: str, turn_num: int, ws_client, coordinator) -> None:
    action_payload = make_decision(view, bot_name)
    act_type = action_payload.get("type", "unknown")
    act_name = action_payload.get("name", "None")
    act_score = action_payload.get("score", 0.0)
    act_report = action_payload.get("strategy_report", "None")
    logger.info(f"[»] {bot_name} executes action: {act_type} -> {act_name} (Score: {act_score:.2f})")
    logger.info(f"[~] {bot_name} strategic plan: {act_report}")
    if act_type != "unknown":
        from ai.Strategy.memory import add_recent_event
        add_recent_event(f"Executed action: {act_type} -> {act_name}")
    if act_type in ("move", "explore", "attack", "use_item", "interact", "rest", "pickup", "equip"):
        ws_client.last_acted_turn = turn_num
        coordinator.bots_state[bot_name]["local_cooldown"] = True
        clean_payload = {k: v for k, v in action_payload.items() if k not in ("name", "score", "strategy_report")}
        wrapped_payload = {
            "type": "action",
            "data": clean_payload
        }
        await ws_client.send(wrapped_payload)

async def process_game_frame(frame: dict, bot_name: str, coordinator: LobbyCoordinator, ws_client) -> bool:
    if not isinstance(frame, dict):
        return True

    msg_type = frame.get("type")
    
    if msg_type in ("agent_view", "turn_advanced"):
        view_data_temp = frame.get("view", {})
        if isinstance(view_data_temp, dict):
            curr_reg_temp = view_data_temp.get("currentRegion", {})
            if isinstance(curr_reg_temp, dict):
                curr_id = curr_reg_temp.get("id")
                curr_name = curr_reg_temp.get("name")
                if curr_id and curr_name:
                    from ai.Strategy.memory import record_region_name
                    record_region_name(curr_id, curr_name)
            regions_dict_temp = view_data_temp.get("regions", {})
            if isinstance(regions_dict_temp, dict):
                from ai.Strategy.memory import record_region_name
                for r_id, r_data in regions_dict_temp.items():
                    if isinstance(r_data, dict):
                        r_name = r_data.get("name")
                        if r_id and r_name:
                            record_region_name(r_id, r_name)

        self_data_temp = view_data_temp.get("self", {})
        if isinstance(self_data_temp, dict):
            new_hp = self_data_temp.get("hp")
            new_kills = self_data_temp.get("kills")
            prev_view = coordinator.bots_state[bot_name].get("view", {})
            if isinstance(prev_view, dict):
                prev_self = prev_view.get("self", {})
                if isinstance(prev_self, dict):
                    prev_hp = prev_self.get("hp")
                    prev_kills = prev_self.get("kills")
                if prev_hp is not None and new_hp is not None and new_hp < prev_hp:
                    from ai.Strategy.memory import add_recent_event
                    add_recent_event(f"Took {prev_hp - new_hp} damage")
                if prev_kills is not None and new_kills is not None and new_kills > prev_kills:
                    from ai.Strategy.memory import add_recent_event
                    add_recent_event("Killed an enemy!")

        inventory = self_data_temp.get("inventory", [])
        equipped_weapon = self_data_temp.get("equippedWeapon")
        equipped_weapon_name = equipped_weapon.get("name", "Fist") if isinstance(equipped_weapon, dict) else "Fist"
        
        MELEE_WEAPONS = {"Katana", "Sword", "Dagger"}
        RANGED_WEAPONS = {"Sniper rifle", "Bow", "Pistol"}
        
        best_melee_atk = get_weapon_atk(equipped_weapon_name) if equipped_weapon_name in MELEE_WEAPONS else 0
        best_ranged_atk = get_weapon_atk(equipped_weapon_name) if equipped_weapon_name in RANGED_WEAPONS else 0
        
        for item in inventory:
            if isinstance(item, dict):
                item_name = item.get("name")
                if item_name in MELEE_WEAPONS:
                    best_melee_atk = max(best_melee_atk, get_weapon_atk(item_name))
                elif item_name in RANGED_WEAPONS:
                    best_ranged_atk = max(best_ranged_atk, get_weapon_atk(item_name))
        
        for item in inventory:
            if isinstance(item, dict):
                item_name = item.get("name")
                item_id = item.get("id")
                if item_name in MELEE_WEAPONS and get_weapon_atk(item_name) < best_melee_atk:
                    from ai.Strategy.memory import add_recent_event
                    add_recent_event(f"Dropped redundant weapon: {item_name}")
                    wrapped_payload = {
                        "type": "action",
                        "data": {"type": "drop", "itemId": item_id}
                    }
                    await ws_client.send(wrapped_payload)
                elif item_name in RANGED_WEAPONS and get_weapon_atk(item_name) < best_ranged_atk:
                    from ai.Strategy.memory import add_recent_event
                    add_recent_event(f"Dropped redundant weapon: {item_name}")
                    wrapped_payload = {
                        "type": "action",
                        "data": {"type": "drop", "itemId": item_id}
                    }
                    await ws_client.send(wrapped_payload)

    turn = frame.get("turn")
    view_data = frame.get("view", {})
    self_data = view_data.get("self") if isinstance(view_data, dict) else None
    
    is_alive = True
    if isinstance(self_data, dict) and self_data:
        is_alive = self_data.get("isAlive", True)
        hp = self_data.get("hp", 100)
        if hp == 0:
            is_alive = False
    else:
        if view_data:
            is_alive = False

    if turn is not None and turn != ws_client.last_logged_turn and is_alive:
        write_gameplay_log(bot_name, f"# Turn {turn}", frame.get("view", {}))
        ws_client.last_logged_turn = turn

    if msg_type in ("agent_view", "turn_advanced"):
        coordinator.bots_state[bot_name]["view"] = frame.get("view", {})
        coordinator.bots_state[bot_name]["turn"] = frame.get("turn", 0)
        await coordinator.draw_table()

    if is_alive is False:
        if not coordinator.bots_state[bot_name].get("alive", True):
            return False
        coordinator.bots_state[bot_name]["alive"] = False
        await coordinator.draw_table()
        turn_num = frame.get("turn") or ws_client.last_logged_turn
        logger.info(f"[-] {bot_name} has been eliminated. Logging turn {turn_num}.")
        if isinstance(view_data, dict):
            if "self" not in view_data:
                view_data["self"] = {}
            view_data["self"]["hp"] = 0
            view_data["self"]["isAlive"] = False
        write_gameplay_log(bot_name, f"# Turn {turn_num}", view_data)
        write_gameplay_log(bot_name, f"[SYSTEM] Agent {bot_name} has been eliminated. Exiting game loop...")
        return False
    else:
        if not coordinator.bots_state[bot_name].get("alive", True):
            coordinator.bots_state[bot_name]["alive"] = True
            await coordinator.draw_table()

    if msg_type == "event":
        event_name = frame.get("event")
        event_data = frame.get("data", {})
        my_agent_id = coordinator.bots_state[bot_name].get("agent_id")
        
        if event_name not in ("agent_died", "game_settled"):
            logger.info(f"[RAW EVENT] {bot_name} received event '{event_name}': {event_data}")

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
                turn_num = frame.get("turn") or ws_client.last_logged_turn
                if turn_num >= 0:
                    write_gameplay_log(bot_name, f"# Turn {turn_num}", latest_view)
                write_gameplay_log(bot_name, f"[SYSTEM] Agent {bot_name} received agent_died event (HP: 0). Exiting game loop...")
                return False
            else:
                from ai.Strategy.memory import add_recent_event
                add_recent_event(f"Player {event_data.get('agentId')} was eliminated")
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
        
    if msg_type == "turn_advanced":
        coordinator.bots_state[bot_name]["local_cooldown"] = False

    if msg_type == "action_result":
        success = frame.get("success", True)
        if not success:
            err = frame.get("error", {})
            logger.warning(f"[!] Action result warning: {err.get('message', 'Unknown')} (Code: {err.get('code', 'None')})")
            coordinator.bots_state[bot_name]["local_cooldown"] = False
            from ai.Strategy.memory import add_recent_event
            add_recent_event(f"Action failed: {err.get('message', 'Unknown error')}")
        res_data = frame.get("data", {})
        if isinstance(res_data, dict):
            if res_data.get("canAct") is True or res_data.get("can_act") is True:
                coordinator.bots_state[bot_name]["local_cooldown"] = False

    if msg_type == "agent_view":
        current_region = frame.get("view", {}).get("currentRegion", {})
        curr_id = current_region.get("id") if isinstance(current_region, dict) else None
        if curr_id:
            from ai.Strategy.memory import mark_visited, record_map_connections
            mark_visited(curr_id)
            record_map_connections(curr_id, current_region.get("connections", []))

        self_data = frame.get("view", {}).get("self")
        is_agent_alive = True
        can_act = True
        if isinstance(self_data, dict) and self_data:
            is_agent_alive = self_data.get("isAlive", True)
            can_act = self_data.get("canAct", self_data.get("can_act", True))
            if self_data.get("hp") == 0:
                is_agent_alive = False
        else:
            is_agent_alive = False

        turn_num = frame.get("turn", 0)
        already_acted = ws_client.last_acted_turn == turn_num
        is_local_cooldown = coordinator.bots_state[bot_name].get("local_cooldown", False)

        if msg_type in ("agent_view", "turn_advanced") and is_agent_alive and can_act and not already_acted and not is_local_cooldown:
            await _execute_decision(frame.get("view", {}), bot_name, turn_num, ws_client, coordinator)

    if msg_type == "can_act_changed" and (frame.get("canAct") is True or frame.get("can_act") is True):
        coordinator.bots_state[bot_name]["local_cooldown"] = False
        stored_view = coordinator.bots_state[bot_name].get("view", {})
        if stored_view:
            self_data = stored_view.get("self")
            is_agent_alive = True
            if isinstance(self_data, dict) and self_data:
                is_agent_alive = self_data.get("isAlive", True)
                if self_data.get("hp") == 0:
                    is_agent_alive = False
            else:
                is_agent_alive = False
                
            stored_view["self"]["canAct"] = True
            stored_view["self"]["can_act"] = True

            turn_num = coordinator.bots_state[bot_name].get("turn", 0)
            already_acted = ws_client.last_acted_turn == turn_num

            if is_agent_alive and not already_acted:
                await _execute_decision(stored_view, bot_name, turn_num, ws_client, coordinator)

    return True