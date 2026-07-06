import os
from collections import deque

def get_ally_names(my_name):
    allies = set()
    for key, value in os.environ.items():
        if key.startswith("BOT") and key.endswith("_NAME"):
            if value and value != my_name:
                allies.add(value)
    return allies

def is_guardian_or_monster(entity_data):
    entity_type = entity_data.get("entity_type")
    if entity_type in ["monster", "npc"]:
        return True
    
    name = entity_data.get("name", "")
    if name.lower() == "guardian" or name.lower() == "hermit" or name.lower().startswith("guardian"):
        return True
        
    if entity_data.get("typeId") in ["guardian", "monster", "npc"]:
        return True
        
    if entity_data.get("isNPC") or entity_data.get("is_npc") or entity_data.get("npc"):
        return True
        
    if entity_data.get("def", 0) == 120 or entity_data.get("maxHp") == 150:
        return True
        
    return False

def parse_enemy_status(agent_view_data, known_entities):
    view = agent_view_data.get("view", {})
    self_data = view.get("self", {})
    my_name = self_data.get("name", "Unknown")
    my_id = self_data.get("id")
    
    current_region = view.get("currentRegion", {})
    current_region_id = current_region.get("id")
    
    ally_names = get_ally_names(my_name)
    
    visible_regions = view.get("visibleRegions", [])
    region_map = {r.get("id"): r for r in visible_regions}
    
    if current_region_id not in region_map and current_region_id:
        region_map[current_region_id] = current_region
        
    distances = {}
    if current_region_id:
        distances[current_region_id] = 0
        queue = deque([current_region_id])
        while queue:
            curr = queue.popleft()
            curr_dist = distances[curr]
            region_data = region_map.get(curr, {})
            for conn in region_data.get("connections", []):
                if conn in region_map and conn not in distances:
                    distances[conn] = curr_dist + 1
                    queue.append(conn)
                    
    layers = {}
    for i in range(4):
        layers[i] = {
            "counts": {"P": 0, "M": 0, "A": 0},
            "agents": [],
            "monsters": []
        }
        
    for entity_id, entity_data in known_entities.items():
        if not entity_data.get("isAlive", True):
            continue

        region_id = entity_data.get("regionId", entity_data.get("region_id"))
        dist = distances.get(region_id)
        
        if dist is None:
            continue
        
        entity_name = entity_data.get("name", "Unknown")
        entity_type = entity_data.get("entity_type", "agent")
        
        is_monster_or_npc = is_guardian_or_monster(entity_data)
        is_agent = ("atk" in entity_data) and not is_monster_or_npc
        
        if is_agent and entity_id != my_id:
            is_ally = entity_name in ally_names
            if is_ally:
                layers[dist]["counts"]["A"] += 1
            else:
                layers[dist]["counts"]["P"] += 1
            
            hp = entity_data.get("hp", 0)
            max_hp = entity_data.get("maxHp", 100)
            ep = entity_data.get("ep", 0)
            max_ep = entity_data.get("maxEp", 10)
            atk = entity_data.get("atk", 0)
            defense = entity_data.get("def", 0)
            kills = entity_data.get("kills", 0)
            
            weapon_data = entity_data.get("equippedWeapon")
            weapon = weapon_data.get("name", "None") if isinstance(weapon_data, dict) else (weapon_data if weapon_data else "None")
            
            armor_data = entity_data.get("equippedArmor")
            armor = armor_data.get("name", "None") if isinstance(armor_data, dict) else (armor_data if armor_data else "None")
            
            layers[dist]["agents"].append({
                "name": entity_name,
                "hp": hp,
                "max_hp": max_hp,
                "ep": ep,
                "max_ep": max_ep,
                "atk": atk,
                "def": defense,
                "kills": kills,
                "weapon": weapon,
                "armor": armor,
                "is_ally": is_ally
            })
        elif is_monster_or_npc and entity_id != my_id:
            layers[dist]["counts"]["M"] += 1
            
            hp_val = entity_data.get("hp", 0)
            is_guardian = "guardian" in entity_name.lower() or "hermit" in entity_name.lower() or entity_data.get("def", 0) == 120 or entity_data.get("maxHp") == 150
            m_type = "Guardian" if is_guardian else "Monster"
            default_max = 150 if is_guardian else 100
            max_hp_val = entity_data.get("maxHp", default_max)
            
            layers[dist]["monsters"].append({
                "name": entity_name,
                "hp": hp_val,
                "max_hp": max_hp_val,
                "is_npc": is_guardian,
                "atk": entity_data.get("atk", 12),
                "def": entity_data.get("def", 120),
                "kills": entity_data.get("kills", 0)
            })
            
    return {
        "layers": layers
    }