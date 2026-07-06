from collections import Counter

def print_turn_log(turn, status, zone_status, loot_status, radar_status, alive_count):
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
    output.append(f"Location: {location} | Terrain: {terrain} | Weather: {weather} | Vision Modifier: {vision_modifier} | Agent Sight Range: {agent_sight_range} | Links: {links}")
    output.append(f"Facilities: {facilities_str}")
    output.append(f"Ground Items ({ground_items_count}): {ground_items_str}")
    output.append("-" * 50)
    
    print("\n".join(output))