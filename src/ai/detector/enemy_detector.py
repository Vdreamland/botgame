import os
from src.game_data import MONSTERS, GUARDIANS
from src.utils import calculate_region_distances

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
    if name in MONSTERS or name in GUARDIANS:
        return True
        
    if any(k in name.lower() for k in ["guardian", "hermit"]):
        return True
        
    if entity_data.get("typeId") in ["guardian", "monster", "npc"]:
        return True
        
    if entity_data.get("isNPC") or entity_data.get("is_npc") or entity_data.get("npc"):
        return True
        
    if entity_data.get("def", 0) == 120 or entity_data.get("maxHp") == 150:
        return True
        
    return False

def parse_enemy_status(agent_view_data, known_entities, distances=None):
    view = agent_view_data.get("view", {})
    self_data = view.get("self", {})
    my_name = self_data.get("name", "Unknown")
    my_id = self_data.get("id")
    
    current_region = view.get("currentRegion", {})
    
    ally_names = get_ally_names(my_name)
    
    visible_regions = view.get("visibleRegions", [])
    
    if distances is None:
        distances = calculate_region_distances(current_region, visible_regions)
                
    max_dist = max(distances.values()) if distances else 0
    layers = {}
    for i in range(max_dist + 1):
        layers[i] = {
            "counts": {"P": 0, "M": 0, "A": 0},
            "agents": [],
            "monsters": []
        }
        
    visible_agent_ids = {a.get("id") for a in view.get("visibleAgents", []) if a.get("id")}
    visible_monster_ids = {m.get("id") for m in view.get("visibleMonsters", []) if m.get("id")}
    visible_npc_ids = {n.get("id") for n in view.get("visibleNPCs", []) if n.get("id")}
    visible_ids = visible_agent_ids | visible_monster_ids | visible_npc_ids
    
    for entity_id, entity_data in known_entities.items():
        if entity_id not in visible_ids:
            continue
        if not entity_data.get("isAlive", True):
            continue
            
        region_id = entity_data.get("regionId", entity_data.get("region_id"))
        dist = distances.get(region_id)
        
        if dist is None:
            continue
            
        entity_name = entity_data.get("name", "Unknown")
        
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
            is_guardian = entity_name in GUARDIANS or "guardian" in entity_name.lower() or "hermit" in entity_name.lower() or entity_data.get("def", 0) == 120 or entity_data.get("maxHp") == 150
            
            default_max = 150 if is_guardian else 100
            if entity_name in GUARDIANS:
                default_max = GUARDIANS[entity_name].get("hp", 150)
            elif entity_name in MONSTERS:
                default_max = MONSTERS[entity_name].get("hp", 100)
                
            max_hp_val = entity_data.get("maxHp", default_max)
            
            layers[dist]["monsters"].append({
                "name": entity_name,
                "hp": hp_val,
                "max_hp": max_hp_val,
                "is_npc": is_guardian,
                "atk": entity_data.get("atk"),
                "def": entity_data.get("def"),
                "kills": entity_data.get("kills", entity_data.get("killCount"))
            })
            
    return {
        "layers": layers
    }