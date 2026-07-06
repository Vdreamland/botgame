def process_combat_message(manager, frame_type, data):
    if frame_type in ["hp_changed", "agent_damaged", "monster_damaged"]:
        target_id = data.get("targetId")
        attacker_id = data.get("attackerId", data.get("agentId"))
        damage = data.get("damage", 0)
    
        entity_id = target_id if target_id else data.get("agentId")
        if entity_id and entity_id in manager.known_entities:
            manager.known_entities[entity_id]["hp"] = data.get("hp", data.get("currentHp", 0))
    
        if hasattr(manager, "my_id") and entity_id == manager.my_id:
            new_hp = data.get("hp", data.get("currentHp", 0))
            manager.status["hp"] = new_hp
            if new_hp == 0:
                manager.status["is_alive"] = False
    
        if damage > 0 and hasattr(manager, "my_id"):
            is_target_me = (entity_id == manager.my_id)
            is_attacker_me = (attacker_id == manager.my_id) and (entity_id != manager.my_id)
    
            if is_target_me or is_attacker_me:
                attacker_name = "Unknown"
                target_name = "Unknown"
    
                if is_target_me:
                    target_name = "You"
                    att_id = data.get("attackerId")
                    if att_id:
                        attacker_name = manager.known_entities.get(att_id, {}).get("name", "An enemy")
                    else:
                        attacker_name = data.get("attackerName", data.get("agentName", "An enemy"))
    
                    if attacker_name in ["Unknown", "An enemy"]:
                        layer_0_agents = manager.enemy_status.get("layers", {}).get(0, {}).get("agents", [])
                        if len(layer_0_agents) == 1:
                            attacker_name = layer_0_agents[0].get("name")
                        else:
                            attacker_name = "An enemy"
                else:
                    attacker_name = "You"
                    target_name = manager.known_entities.get(entity_id, {}).get("name", "An enemy")
    
                weapon_val = data.get("weapon")
                weapon_name = "None"
                if isinstance(weapon_val, dict):
                    weapon_name = weapon_val.get("name", "None")
                elif isinstance(weapon_val, str):
                    weapon_name = weapon_val
                elif attacker_id and attacker_id in manager.known_entities:
                    w_data = manager.known_entities[attacker_id].get("equippedWeapon")
                    if w_data:
                        weapon_name = w_data.get("name", "None") if isinstance(w_data, dict) else w_data
    
                region_id = manager.status.get("region_id")
                region_name = manager.region_name_map.get(region_id, "Unknown Region")
    
                dist = manager.current_distances.get(region_id, 0)
                layer_str = f"Layer {dist}" if dist > 0 else "Same Region"
    
                if is_target_me:
                    log_msg = f"{attacker_name} attacked You for {damage} damage using {weapon_name} from {region_name} ({layer_str})"
                else:
                    log_msg = f"You attacked {target_name} for {damage} damage using {weapon_name} in {region_name} ({layer_str})"
    
                manager.fight_history.append(log_msg)
                if len(manager.fight_history) > 10:
                    manager.fight_history.pop(0)
    
    elif frame_type in ["agent_died", "monster_killed"]:
        entity_id = data.get("targetId", data.get("agentId"))
        attacker_id = data.get("attackerId")
    
        if entity_id and entity_id in manager.known_entities:
            entity_data = manager.known_entities[entity_id]
            region_id = entity_data.get("regionId", entity_data.get("region_id"))
    
            if hasattr(manager, "my_id") and attacker_id == manager.my_id:
                current_region_id = manager.status.get("region_id")
                if region_id and region_id != current_region_id:
                    if region_id not in manager.pending_loot_regions:
                        manager.pending_loot_regions.append(region_id)
    
            manager.known_entities[entity_id]["hp"] = 0
            manager.known_entities[entity_id]["isAlive"] = False
    
        if hasattr(manager, "my_id") and entity_id == manager.my_id:
            manager.status["hp"] = 0
            manager.status["is_alive"] = False
    
    elif frame_type == "ep_changed":
        entity_id = data.get("targetId", data.get("agentId"))
        new_ep = data.get("ep", data.get("currentEp", 0))
        if hasattr(manager, "my_id") and entity_id == manager.my_id:
            manager.status["ep"] = new_ep
    
    elif frame_type == "action_result":
        success = data.get("success", True)
        manager.can_act = data.get("canAct", not success)