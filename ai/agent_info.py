from ai.skill.vision import get_layered_zones
from ai.detector.zone_detector import detect_terrain, detect_weather
from ai.detector.dead_zone_detector import analyze_death_zones
from ai.detector.ground_detector import detect_ground_loot
from game_data.world_info import TERRAINS

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
    
    current_region = view_data.get("currentRegion", {})
    location_name = current_region.get("name", "Unknown")
    
    raw_terrain = detect_terrain(current_region)
    terrain_name = str(raw_terrain).capitalize()
    
    weather_name = str(detect_weather(view_data)).capitalize()
    
    terrain_key = str(raw_terrain).lower()
    vision_mod = TERRAINS.get(terrain_key, {}).get("vision_modifier", 0)
    
    links_count = len(current_region.get("connections", []))
    
    dead_zone_names = []
    if current_region.get("isDeathZone"):
        if location_name and location_name != "Unknown":
            dead_zone_names.append(location_name)
            
    regions = view_data.get("regions", {})
    for r_id, r_data in regions.items():
        if r_id == current_region.get("id"):
            continue
        if r_data.get("isDeathZone"):
            name = r_data.get("name")
            if name:
                dead_zone_names.append(name)
                
    dead_zone_display = ", ".join(dead_zone_names) if dead_zone_names else "None"
    
    loot_list = detect_ground_loot(view_data)
    ground_loot_display = ", ".join(loot_list) if loot_list else "None"
    
    return (
        f"# Turn {turn} [{bot_name}]\n"
        f"HP: {hp} | EP: {ep} | Atk: {atk} | Def: {defense} | Kills: {kills} | Vision : {vision_zones} Zone\n"
        f"Equipped : Weapon : {weapon_name} | Armour : {armour_name}\n"
        f"Inventory {inv_slots_used}/10 : {inv_display}\n"
        f"Location : {location_name} | Terrain: {terrain_name} | Weather : {weather_name} | Vision {vision_mod} | Links {links_count}\n"
        f"DeadZone : {dead_zone_display}\n"
        f"Ground Loot : {ground_loot_display}"
    )