from utils.logger import logger
from ai.Strategy import make_decision

async def execute_decision(view: dict, bot_name: str, turn_num: int, ws_client, coordinator) -> None:
    from ai.detector.enemy_detector import get_detailed_enemy_stats
    detailed = get_detailed_enemy_stats(view, bot_name)
    players = detailed.get("players", [])
    monsters = detailed.get("monsters", [])
    for p in players:
        p_lay = p.get("layer")
        display_lay = "Far (Unreachable)" if p_lay == -1 else p_lay
        logger.info(f"[DETECTOR] Enemy Player: {p.get('name')} | HP: {p.get('hp')} | EP: {p.get('ep')} | ATK: {p.get('atk')} | DEF: {p.get('def')} | Weapon: {p.get('weapon')} | Armour: {p.get('armour')} | Layer: {display_lay}")
    for m in monsters:
        m_lay = m.get("layer")
        display_lay = "Far (Unreachable)" if m_lay == -1 else m_lay
        logger.info(f"[DETECTOR] Enemy Monster: {m.get('type') or m.get('name')} | HP: {m.get('hp')} | Layer: {display_lay}")

    action_payload = make_decision(view, bot_name)
    act_type = action_payload.get("type", "unknown")
    act_name = action_payload.get("name", "None")
    act_score = action_payload.get("score", 0.0)
    act_report = action_payload.get("strategy_report", "None") 

    self_data = view.get("self", {})
    inventory = self_data.get("inventory", []) 

    if act_type == "pickup" and len(inventory) >= 10:
        discard_item_id = None
        discard_item_name = None
        for discard_candidate in ("Bandage", "Emergency Food", "Energy drink", "Energy Drink", "Medkit", "medkit"):
            for item in inventory:
                if isinstance(item, dict) and item.get("name") == discard_candidate:
                    discard_item_id = item.get("id")
                    discard_item_name = item.get("name")
                    break
            if discard_item_id:
                break
        if discard_item_id:
            logger.info(f"[*] Inventory full (10/10). Proactively dropping least important item '{discard_item_name}' to free up slot for pickup.")
            from ai.Strategy.memory import add_recent_event
            add_recent_event(f"Proactively dropped {discard_item_name} to free slot")
            drop_payload = {
                "type": "action",
                "data": {"type": "drop", "itemId": discard_item_id}
            }
            await ws_client.send(drop_payload)
            coordinator.bots_state[bot_name]["local_cooldown"] = True
            return

    logger.info(f"[»] {bot_name} executes action: {act_type} -> {act_name} (Score: {act_score:.2f})")
    logger.info(f"[~] {bot_name} strategic plan: {act_report}")
    if act_type != "unknown":
        from ai.Strategy.memory import add_recent_event
        add_recent_event(f"Executed action: {act_type} -> {act_name}")
    if act_type in ("move", "explore", "attack", "use_item", "interact", "rest", "pickup", "equip"):
        clean_payload = {k: v for k, v in action_payload.items() if k not in ("name", "score", "strategy_report")}
        wrapped_payload = {
            "type": "action",
            "data": clean_payload
        }
        await ws_client.send(wrapped_payload)
        coordinator.bots_state[bot_name]["local_cooldown"] = True
        major_actions = {"move", "explore", "attack", "rest", "interact"}
        if act_type in major_actions:
            ws_client.last_acted_turn = turn_num