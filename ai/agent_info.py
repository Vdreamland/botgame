from ai.skill.vision import get_layered_zones

def format_agent_status_log(bot_name: str, turn: int, view_data: dict) -> str:
    if not isinstance(view_data, dict):
        return ""
    
    self_data = view_data.get("self", {})
    hp = self_data.get("hp", 100)
    ep = self_data.get("ep", 10)
    atk = self_data.get("atk", 25)
    defense = self_data.get("def", 5)
    kills = self_data.get("kills", 0)
    
    vision_info = get_layered_zones(view_data)
    vision_zones = vision_info.get("total_visible_zones", 0)
    
    eq_weapon = view_data.get("equippedWeapon")
    weapon_name = "None"
    if isinstance(eq_weapon, dict):
        weapon_name = eq_weapon.get("name", "None")
        
    eq_armour = view_data.get("equippedArmor")
    armour_name = "None"
    if isinstance(eq_armour, dict):
        armour_name = eq_armour.get("name", "None")
        
    inventory = view_data.get("inventory", [])
    inv_slots_used = len(inventory)
    
    inv_counts = {}
    for item in inventory:
        if isinstance(item, dict):
            name = item.get("name", "Unknown")
            inv_counts[name] = inv_counts.get(name, 0) + 1
            
    inv_display = ", ".join([f"{name} [{count}]" for name, count in inv_counts.items()]) if inv_counts else "None"
    
    return (
        f"# Turn {turn} [{bot_name}]\n"
        f"HP: {hp} | EP: {ep} | Atk: {atk} | Def: {defense} | Kills: {kills} | Vision : {vision_zones} Zone\n"
        f"Equipped : Weapon : {weapon_name} | Armour : {armour_name}\n"
        f"Inventory {inv_slots_used}/10 : {inv_display}"
    )