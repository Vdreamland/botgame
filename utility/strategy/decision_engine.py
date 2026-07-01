# utility/strategy/decision_engine.py

from utility.strategy.combat_solver import evaluate_combat_targets
from utility.strategy.loot_solver import evaluate_loot_desire
from utility.strategy.movement_solver import evaluate_movement_routes

def make_decision(bot_name: str, self_data: dict, current_region: dict, view_data: dict, joined_bots: list, log_state: dict) -> dict:
    """Otak Utama (Desire Scorer) yang menimbang hasrat taktis dan merangkai urutan eksekusi tindakan turn terbaik"""
    
    combat_res = evaluate_combat_targets(bot_name, self_data, current_region, view_data, joined_bots)
    loot_res = evaluate_loot_desire(bot_name, self_data, current_region, view_data, joined_bots, log_state)
    move_res = evaluate_movement_routes(bot_name, self_data, current_region, view_data, joined_bots, log_state)
    
    our_hp = self_data.get("hp", 100)
    our_max_hp = self_data.get("maxHp") or self_data.get("max_hp") or 100
    our_ep = self_data.get("ep", 10)
    our_max_ep = self_data.get("maxEp") or self_data.get("max_ep") or 10
    
    heal_desire = 0.0
    best_heal_item_id = None
    
    inventory = self_data.get("inventory") or []
    heal_items = []
    
    for item in inventory:
        item_id = None
        item_name = ""
        
        if isinstance(item, dict):
            item_id = item.get("id") or item.get("instanceId") or item.get("instance_id")
            item_name = (item.get("displayName") or item.get("name") or "").lower()
        elif isinstance(item, str):
            item_id = item
            item_name = item.lower()
            
        if item_id and ("medkit" in item_name or "bandage" in item_name or "food" in item_name):
            heal_items.append((item_id, item_name))
            
    if heal_items and our_hp < 75:
        heal_items.sort(key=lambda x: "medkit" in x[1], reverse=True)
        best_heal_item_id = heal_items[0][0]
        heal_desire = (75 - our_hp) * 1.3
        heal_desire = min(100.0, heal_desire)
        
    rest_desire = 0.0
    is_in_danger = current_region.get("isDeathZone") or current_region.get("is_death_zone") or (current_region.get("id") in [pz.get("id") for pz in view_data.get("pendingDeathzones", []) if isinstance(pz, dict)])
    
    if our_ep < 3:
        if not is_in_danger:
            rest_desire = 110.0
        else:
            threat_penalty = 50 if combat_res["can_attack"] else 0
            rest_desire = max(0.0, (10 - our_ep) * 10 - threat_penalty)
        
    attack_score = combat_res["best_target"]["priority_score"] / 15 if combat_res["can_attack"] and combat_res["best_target"] else 0.0
    attack_score = min(100.0, max(0.0, attack_score))
    
    loot_score = loot_res["loot_desire"]
    move_score = move_res["move_desire"]
    
    interact_score = 0.0
    best_facility = loot_res.get("best_facility")
    if best_facility:
        interact_score = max(0.0, best_facility.get("ev", 0.0))
        
    desires = [
        ("attack", attack_score),
        ("heal", heal_desire),
        ("loot", loot_score),
        ("move", move_score),
        ("rest", rest_desire),
        ("interact", interact_score)
    ]
    
    desires.sort(key=lambda x: x[1], reverse=True)
    chosen_strategy = desires[0][0]
    
    free_equips = []
    
    equipped_weapon = self_data.get("equippedWeapon")
    current_weapon_atk = -1
    if isinstance(equipped_weapon, dict):
        w_name = (equipped_weapon.get("name") or "").lower()
        if w_name and w_name != "fist":
            if "sniper" in w_name or "rifle" in w_name:
                current_weapon_atk = 35
            elif "katana" in w_name:
                current_weapon_atk = 25
            elif "sword" in w_name or "bow" in w_name:
                current_weapon_atk = 15
            elif "pistol" in w_name or "gun" in w_name:
                current_weapon_atk = 10
            elif "dagger" in w_name:
                current_weapon_atk = 5
            else:
                current_weapon_atk = 0
    elif isinstance(equipped_weapon, str):
        w_name = equipped_weapon.lower()
        if w_name not in ("none", "fist"):
            if "sniper" in w_name or "rifle" in w_name:
                current_weapon_atk = 35
            elif "katana" in w_name:
                current_weapon_atk = 25
            elif "sword" in w_name or "bow" in w_name:
                current_weapon_atk = 15
            elif "pistol" in w_name or "gun" in w_name:
                current_weapon_atk = 10
            elif "dagger" in w_name:
                current_weapon_atk = 5
            else:
                current_weapon_atk = 0

    equipped_armor = self_data.get("equippedArmor")
    current_armor_def = -1
    if isinstance(equipped_armor, dict):
        a_name = (equipped_armor.get("name") or "").lower()
        if a_name and a_name != "none":
            current_armor_def = equipped_armor.get("defBonus") or equipped_armor.get("def_bonus") or 0
            if current_armor_def == 0:
                if "plate" in a_name:
                    current_armor_def = 4
                elif "chainmail" in a_name:
                    current_armor_def = 2
                elif "leather" in a_name:
                    current_armor_def = 1
    elif isinstance(equipped_armor, str):
        a_name = equipped_armor.lower()
        if a_name != "none":
            if "plate" in a_name:
                current_armor_def = 4
            elif "chainmail" in a_name:
                current_armor_def = 2
            elif "leather" in a_name:
                current_armor_def = 1
            else:
                current_armor_def = 0

    best_inv_weapon_id = None
    best_inv_weapon_atk = current_weapon_atk

    best_inv_armor_id = None
    best_inv_armor_def = current_armor_def
            
    for item in inventory:
        item_id = None
        item_name = ""
        def_bonus_val = None
        item_type = None
        
        if isinstance(item, dict):
            item_id = item.get("id") or item.get("instanceId") or item.get("instance_id")
            item_name = (item.get("displayName") or item.get("name") or "").lower()
            def_bonus_val = item.get("defBonus") or item.get("def_bonus")
            item_type = item.get("type") or item.get("category")
        elif isinstance(item, str):
            item_id = item
            item_name = item.lower()
            
        if not item_id:
            continue
            
        is_weapon = "sword" in item_name or "dagger" in item_name or "katana" in item_name or "bow" in item_name or "pistol" in item_name or "sniper" in item_name or "fist" in item_name or "gun" in item_name or "rifle" in item_name or item_type == "weapon"
        is_armor = "armor" in item_name or "leather" in item_name or "chainmail" in item_name or "plate" in item_name or "vest" in item_name or "robe" in item_name or item_type == "armor" or def_bonus_val is not None
        
        if is_weapon:
            atk_val = 0
            if "sniper" in item_name or "rifle" in item_name:
                atk_val = 35
            elif "katana" in item_name:
                atk_val = 25
            elif "sword" in item_name or "bow" in item_name:
                atk_val = 15
            elif "pistol" in item_name or "gun" in item_name:
                atk_val = 10
            elif "dagger" in item_name:
                atk_val = 5
                
            if atk_val > best_inv_weapon_atk:
                best_inv_weapon_atk = atk_val
                best_inv_weapon_id = item_id
                
        elif is_armor:
            def_val = 0
            if def_bonus_val is not None:
                def_val = def_bonus_val
            else:
                if "plate" in item_name:
                    def_val = 4
                elif "chainmail" in item_name:
                    def_val = 2
                elif "leather" in item_name:
                    def_val = 1
                    
            if def_val > best_inv_armor_def:
                best_inv_armor_def = def_val
                best_inv_armor_id = item_id

    if best_inv_weapon_id:
        free_equips.append(best_inv_weapon_id)
    if best_inv_armor_id:
        free_equips.append(best_inv_armor_id)
                
    action_data = None
    thought_string = f"Taktis: Memilih strategi '{chosen_strategy}' dengan bobot evaluasi tertinggi."
    
    free_pickups = []
    if loot_res["items_to_pickup"]:
        free_pickups = loot_res["items_to_pickup"][:3]
        
    if chosen_strategy == "attack" and combat_res["best_target"]:
        target_id = combat_res["best_target"].get("id") or combat_res["best_target"].get("name")
        action_data = {
            "type": "attack",
            "targetId": target_id
        }
        target_display_name = combat_res["best_target"].get("name")
        thought_string = f"Menyerang musuh '{target_display_name}' karena peluang menang sangat besar."
        
    elif chosen_strategy == "heal" and best_heal_item_id:
        action_data = {
            "type": "use_item",
            "itemId": best_heal_item_id
        }
        thought_string = f"Melakukan pemulihan menggunakan item penyembuh karena HP kritis ({our_hp})."
        
    elif chosen_strategy == "loot" and free_pickups:
        action_data = {
            "type": "pickup",
            "itemId": free_pickups[0]
        }
        thought_string = "Fokus menyapu bersih koin sMoltz dan barang berharga di lobi lantai."
        
    elif chosen_strategy == "interact" and best_facility:
        f_id = best_facility.get("id")
        action_data = {
            "type": "interact",
            "facilityId": f_id,
            "id": f_id
        }
        
        if "attempted_facilities" not in log_state:
            log_state["attempted_facilities"] = {}
        log_state["attempted_facilities"][f_id] = log_state["attempted_facilities"].get(f_id, 0) + 1
        
        thought_string = f"Menggunakan fasilitas '{best_facility.get('type').replace('_', ' ').title()}' di wilayah ini untuk keuntungan taktis."
        
    elif chosen_strategy == "move" and move_res["best_region_id"]:
        dest_id = move_res["best_region_id"]
        dest_name = move_res["best_region_name"]
        action_data = {
            "type": "move",
            "regionId": dest_id
        }
        thought_string = f"Mengatur navigasi rute bergerak menuju '{dest_name}' demi keamanan taktis."
        
        if "visited_regions" not in log_state:
            log_state["visited_regions"] = []
        log_state["visited_regions"].append(dest_id)
        if len(log_state["visited_regions"]) > 10:
            log_state["visited_regions"].pop(0)
            
    elif chosen_strategy == "rest":
        action_data = {
            "type": "rest"
        }
        thought_string = f"Melakukan istirahat sejenak untuk memulihkan energi EP (EP: {our_ep})."
        
    else:
        if move_res["best_region_id"]:
            action_data = {
                "type": "move",
                "regionId": move_res["best_region_id"]
            }
            thought_string = "Melakukan manuver pergerakan darurat demi keselamatan."
        else:
            action_data = {
                "type": "rest"
            }
            thought_string = "Semua rute terblokir atau tidak aman. Berdiam diri menimbun energi."
            
    return {
        "action": action_data,
        "free_pickups": free_pickups,
        "free_equips": free_equips,
        "thought": thought_string
    }