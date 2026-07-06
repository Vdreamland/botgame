from collections import Counter

def print_turn_log(turn, status, zone_status, loot_status, radar_status, enemy_status, alive_count, fight_history=None):
    name = status.get("name", "Unknown")
    hp = status.get("hp", 0)
    max_hp = status.get("max_hp", 100)
    ep = status.get("ep", 0)
    max_ep = status.get("max_ep", 10)
    is_alive_bool = status.get("is_alive", True)
    is_alive = "Alive" if is_alive_bool else "Dead"
    location = zone_status.get("location", "Unknown")
    
    atk = status.get("atk", 0)
    defense = status.get("def", 0)
    kills = status.get("kills", 0)
    personal_vision = status.get("vision", 0)
    
    weapon_data = status.get("equipped_weapon")
    weapon_name = weapon_data.get("name") if weapon_data else "None"
    
    armor_data = status.get("equipped_armor")
    armor_name = armor_data.get("name") if armor_data else "None"
    
    inventory_list = status.get("inventory", [])
    
    slots_used = sum(1 for item in inventory_list if item != "sMoltz")
    if "sMoltz" in inventory_list:
        slots_used += 1
        
    counts = Counter(inventory_list)
    grouped_items = []
    for item_name, count in counts.items():
        grouped_items.append(f"{item_name} [{count}]")
        
    if grouped_items:
        inventory_str = ", ".join(grouped_items)
    else:
        inventory_str = "Empty"
        
    terrain = zone_status.get("terrain", "plains").capitalize()
    weather = zone_status.get("weather", "clear").capitalize()
    links = zone_status.get("links_count", 0)
    vision_modifier = zone_status.get("vision_modifier", 0)
    agent_sight_range = max(0, personal_vision + vision_modifier)
    
    facilities = zone_status.get("facilities", [])
    facilities_str = ", ".join(facilities) if facilities else "None"
    
    ground_items_list = loot_status.get("ground_items", [])
    ground_items_count = loot_status.get("ground_item_count", 0)
    
    ground_counts = Counter(ground_items_list)
    grouped_ground = []
    for item_name, count in ground_counts.items():
        grouped_ground.append(f"{item_name} [{count}]")
        
    if grouped_ground:
        ground_items_str = ", ".join(grouped_ground)
    else:
        ground_items_str = "None"
        
    output = []
    output.append("\n" + "-" * 50)
    output.append(f"Turn: {turn} | {name} [{is_alive}]")
    output.append(f"HP: {hp}/{max_hp} | EP: {ep}/{max_ep} | Remaining Players: {alive_count}")
    output.append(f"ATK: {atk} | DEF: {defense} | Kills: {kills}")
    output.append(f"Weapon: {weapon_name} | Armor: {armor_name}")
    output.append(f"Inventory ({slots_used}/10): {inventory_str}")
    output.append("")
    output.append(f"Location: {location} | Terrain: {terrain} | Weather: {weather} | Vision: {vision_modifier} | Agent Sight Range: {agent_sight_range} | Links: {links}")
    output.append(f"Facilities: {facilities_str}")
    output.append(f"Ground Items ({ground_items_count}): {ground_items_str}")
    
    if fight_history:
        output.append("")
        output.append("Fight History:")
        for log_entry in fight_history:
            output.append(f"  -> {log_entry}")
            
    layers = radar_status.get("layers", {})
    has_visible_layers = any(len(layers[dist]) > 0 for dist in layers if dist > 0)
    
    output.append("")
    if has_visible_layers:
        output.append("Radar:")
        for dist in sorted(layers.keys()):
            if dist == 0:
                continue
            if layers[dist]:
                region_names = ", ".join(layers[dist])
                output.append(f"Layer {dist}: {region_names}")
    else:
        output.append("Radar: None")
        
    enemy_layers = enemy_status.get("layers", {})
    output.append("")
    
    has_any_enemies = False
    for dist in enemy_layers:
        layer_data = enemy_layers[dist]
        c = layer_data.get("counts", {"P": 0, "M": 0, "A": 0})
        if c["P"] > 0 or c["M"] > 0 or c["A"] > 0:
            has_any_enemies = True
            break
            
    if has_any_enemies:
        output.append("Enemy:")
        for dist in sorted(enemy_layers.keys()):
            layer_data = enemy_layers[dist]
            c = layer_data.get("counts", {"P": 0, "M": 0, "A": 0})
            if c["P"] == 0 and c["M"] == 0 and c["A"] == 0:
                continue
                
            output.append(f"Layer {dist} : P: {c['P']} | M: {c['M']} | A: {c['A']}")
            
            for agent in layer_data.get("agents", []):
                a_name = agent.get("name")
                hp_val = agent.get("hp")
                max_hp_val = agent.get("max_hp")
                ep_val = agent.get("ep")
                max_ep_val = agent.get("max_ep")
                atk_val = agent.get("atk")
                def_val = agent.get("def")
                kills_val = agent.get("kills")
                w_name = agent.get("weapon")
                arm_name = agent.get("armor")
                role = "Ally" if agent.get("is_ally") else "Enemy"
                
                output.append(f"  -> [{role}] {a_name} | HP: {hp_val}/{max_hp_val} | EP: {ep_val}/{max_ep_val} | ATK: {atk_val} | DEF: {def_val} | Kills: {kills_val} | Weapon: {w_name} | Armor: {arm_name}")
                
            for monster in layer_data.get("monsters", []):
                m_name = monster.get("name")
                hp_val = monster.get("hp")
                max_hp_val = monster.get("max_hp")
                is_npc = monster.get("is_npc", False)
                
                if is_npc:
                    m_atk = monster.get("atk")
                    m_def = monster.get("def")
                    m_kills = monster.get("kills")
                    
                    atk_str = str(m_atk) if m_atk is not None else "?"
                    def_str = str(m_def) if m_def is not None else "?"
                    kills_str = str(m_kills) if m_kills is not None else "0"
                    
                    output.append(f"  -> [Guardian] {m_name} | HP: {hp_val}/{max_hp_val} | ATK: {atk_str} | DEF: {def_str} | Kills: {kills_str}")
                else:
                    output.append(f"  -> [Monster] {m_name} | HP: {hp_val}/{max_hp_val}")
    else:
        output.append("Enemy: None")
        
    output.append("-" * 50)
    
    print("\n".join(output))