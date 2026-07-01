# utility/strategy/loot_solver.py

from utility.detector.layer_detector import calculate_distances
from utility.detector.bot_stats_detector import detect_agent_stats
from utility.detector.inventory_detector import detect_agent_inventory

def evaluate_loot_desire(bot_name: str, self_data: dict, current_region: dict, view_data: dict, joined_bots: list, log_state: dict) -> dict:
    """Mengevaluasi nilai kelayakan penjarahan koin sMoltz atau item di tanah berdasarkan Need, Risk, dan Expected Value"""
    
    ground_items = current_region.get("items") or current_region.get("groundItems") or []
    facilities = current_region.get("interactables") or current_region.get("facilities") or []
    
    our_stats = detect_agent_stats(self_data)
    our_hp = our_stats["hp"]
    our_max_hp = our_stats["max_hp"]
    
    our_inv = detect_agent_inventory(self_data)
    slot_count = our_inv["slot_count"]
    is_inventory_full = slot_count >= 10
    
    distances = calculate_distances(current_region, view_data)
    risk_score = 0
    
    visible_agents = view_data.get("visibleAgents") or []
    for agent in visible_agents:
        if isinstance(agent, dict):
            a_name = agent.get("name")
            if a_name == bot_name:
                continue
                
            is_alive = agent.get("isAlive")
            if is_alive is None:
                is_alive = agent.get("is_alive", True)
                
            if is_alive:
                r_id = agent.get("regionId") or agent.get("region_id")
                dist = distances.get(r_id)
                if dist is not None:
                    if dist == 0:
                        risk_score += 60
                    elif dist == 1:
                        risk_score += 30
                    elif dist == 2:
                        risk_score += 10
                        
    visible_monsters = view_data.get("visibleMonsters") or []
    for monster in visible_monsters:
        if isinstance(monster, dict):
            is_alive = monster.get("isAlive") or monster.get("is_alive", True)
            if is_alive:
                r_id = monster.get("regionId") or monster.get("region_id")
                dist = distances.get(r_id)
                if dist is not None:
                    if dist == 0:
                        risk_score += 40
                    elif dist == 1:
                        risk_score += 20
                        
    is_dz = current_region.get("isDeathZone") or current_region.get("is_death_zone")
    if is_dz:
        risk_score += 30
        
    risk_score = min(100, risk_score)
    
    has_weapon = False
    equipped_weapon = self_data.get("equippedWeapon")
    if isinstance(equipped_weapon, dict):
        w_name = (equipped_weapon.get("name") or "").lower()
        if w_name and w_name != "fist":
            has_weapon = True
    elif isinstance(equipped_weapon, str):
        if equipped_weapon.lower() not in ("none", "fist"):
            has_weapon = True

    has_armor = False
    equipped_armor = self_data.get("equippedArmor")
    if isinstance(equipped_armor, dict):
        a_name = (equipped_armor.get("name") or "").lower()
        if a_name and a_name != "none":
            has_armor = True
    elif isinstance(equipped_armor, str):
        if equipped_armor.lower() != "none":
            has_armor = True
            
    best_facility = None
    max_facility_ev = -999.0
    for f in facilities:
        if not isinstance(f, dict):
            continue
            
        f_type = (f.get("type") or f.get("id") or "").lower()
        f_used = f.get("isUsed") or f.get("is_used") or False
        
        if f_used:
            continue
            
        fac_ev = -999.0
        if is_dz:
            fac_ev = -50.0
        else:
            if "medical" in f_type:
                missing_hp = our_max_hp - our_hp
                if missing_hp > 10:
                    fac_ev = min(98.0, missing_hp * 2.5)
                else:
                    fac_ev = 0.0
            elif "supply" in f_type:
                if not has_weapon:
                    fac_ev = 95.0
                elif not has_armor:
                    fac_ev = 90.0
                elif not is_inventory_full:
                    fac_ev = 45.0
                else:
                    fac_ev = 5.0
            elif "broadcast" in f_type:
                fac_ev = 10.0 if our_stats.get("ep", 0) > 5 else 0.0
                
        if fac_ev > max_facility_ev:
            max_facility_ev = fac_ev
            best_facility = {
                "id": f.get("id") or f.get("type") or "facility",
                "type": f_type,
                "ev": fac_ev
            }
            
    items_to_pickup = []
    total_desire_score = 0.0
    items_count = 0
    
    for item in ground_items:
        if not isinstance(item, dict):
            continue
            
        item_id = item.get("id") or item.get("instanceId")
        item_name = (item.get("displayName") or item.get("name") or "").lower()
        
        item_type = "utility"
        if "food" in item_name or "bandage" in item_name or "medkit" in item_name or "drink" in item_name:
            item_type = "recovery"
        elif "smoltz" in item_name or "moltz" in item_name:
            item_type = "currency"
        elif "sword" in item_name or "dagger" in item_name or "katana" in item_name or "bow" in item_name or "pistol" in item_name or "sniper" in item_name:
            item_type = "weapon"
        elif "armor" in item_name or "leather" in item_name or "chainmail" in item_name:
            item_type = "armor"
            
        item_value = 50
        need_score = 50
        
        if item_type == "currency":
            item_value = 100
            need_score = 100
        elif is_inventory_full:
            item_value = 10
            need_score = 0
        else:
            if item_type == "weapon":
                need_score = 100 if not has_weapon else 15
                item_value = 80 if "katana" in item_name or "sniper" in item_name else 40
            elif item_type == "armor":
                need_score = 90 if not has_armor else 20
                item_value = 70
            elif item_type == "recovery":
                hp_ratio = our_hp / our_max_hp
                need_score = int((1.0 - hp_ratio) * 100)
                item_value = 60 if "medkit" in item_name else 30
                
        success_chance = (100 - risk_score) / 100.0
        failure_chance = risk_score / 100.0
        
        reward = need_score + item_value
        penalty = 80 if item_type != "currency" else 10
        
        expected_value = (reward * success_chance) - (penalty * failure_chance)
        
        is_defenseless = (item_type == "weapon" and not has_weapon) or (item_type == "armor" and not has_armor)
        
        if expected_value > 20 or is_defenseless:
            items_to_pickup.append(item_id)
            total_desire_score += max(30.0, expected_value) if is_defenseless else expected_value
            items_count += 1
            
    loot_desire = min(100.0, max(0.0, total_desire_score / items_count)) if items_count > 0 else 0.0
    action_recommendation = "pickup" if items_to_pickup and loot_desire > 40 else "ignore"
    
    return {
        "loot_desire": loot_desire,
        "items_to_pickup": items_to_pickup,
        "action_recommendation": action_recommendation,
        "estimated_ev": total_desire_score,
        "best_facility": best_facility
    }