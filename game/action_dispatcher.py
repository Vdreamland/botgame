from utils.logger import logger
from ai.Strategy import make_decision

async def execute_decision(view: dict, bot_name: str, turn_num: int, ws_client, coordinator) -> None:
    from ai.detector.enemy_detector import get_detailed_enemy_stats
    detailed = get_detailed_enemy_stats(view, bot_name)
    players = detailed.get("players", [])
    monsters = detailed.get("monsters", [])
    for p in players:
        logger.info(f"[DETECTOR] Enemy Player: {p.get('name')} | HP: {p.get('hp')} | EP: {p.get('ep')} | ATK: {p.get('atk')} | DEF: {p.get('def')} | Weapon: {p.get('weapon')} | Armour: {p.get('armour')} | Layer: {p.get('layer')}")
    for m in monsters:
        logger.info(f"[DETECTOR] Enemy Monster: {m.get('type') or m.get('name')} | HP: {m.get('hp')} | Layer: {m.get('layer')}")

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
            inventory = [i for i in inventory if isinstance(i, dict) and i.get("id") != discard_item_id]

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
        
        if act_type == "pickup":
            MELEE_WEAPONS = {"Katana", "Sword", "Dagger"}
            RANGED_WEAPONS = {"Sniper rifle", "Bow", "Pistol"}
            ARMOURS = {"Plate Armor", "Iron Armor", "Leather Armor", "Chainmail"}
            
            is_gear = act_name in MELEE_WEAPONS or act_name in RANGED_WEAPONS or act_name in ARMOURS or any(g in act_name for g in ("Common", "Rare", "Epic", "Legendary"))
            if is_gear:
                item_id = clean_payload.get("itemId")
                if item_id:
                    logger.info(f"[*] Auto-equipping newly picked up gear '{act_name}' in the same turn.")
                    from ai.Strategy.memory import add_recent_event
                    add_recent_event(f"Auto-equipped: {act_name}")
                    equip_payload = {
                        "type": "action",
                        "data": {
                            "type": "equip",
                            "itemId": item_id
                        }
                    }
                    await ws_client.send(equip_payload)