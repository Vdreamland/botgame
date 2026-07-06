from collections import Counter

def print_turn_log(turn, status, alive_count):
    name = status.get("name", "Unknown")
    hp = status.get("hp", 0)
    max_hp = status.get("max_hp", 100)
    ep = status.get("ep", 0)
    max_ep = status.get("max_ep", 10)
    is_alive_bool = status.get("is_alive", True)
    is_alive = "Alive" if is_alive_bool else "Dead"
    region_id = status.get("region_id", "Unknown")
    
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
        if count > 1:
            grouped_items.append(f"{item_name} [{count}]")
        else:
            grouped_items.append(item_name)
            
    if grouped_items:
        inventory_str = ", ".join(grouped_items)
    else:
        inventory_str = "Empty"
        
    output = []
    output.append("\n" + "-" * 50)
    output.append(f"Turn: {turn} | {name} [{is_alive}] | Region: {region_id}")
    output.append(f"HP: {hp}/{max_hp} | EP: {ep}/{max_ep} | Remaining Players: {alive_count}")
    output.append(f"Weapon: {weapon_name} | Armor: {armor_name}")
    output.append(f"Inventory ({slots_used}/10): {inventory_str}")
    output.append("-" * 50)
    
    print("\n".join(output))