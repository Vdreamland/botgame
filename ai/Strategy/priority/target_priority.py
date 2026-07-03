from ai.detector.enemy_detector import get_detailed_enemy_stats
from game_data.weapon_info import WEAPONS
from game_data.armour_info import ARMOUR_GRADES
from ai.detector.dead_zone_detector import is_dead_zone

def get_weapon_atk(w_name: str) -> int:
    return WEAPONS.get(w_name, {}).get("atk_bonus", 0)

def get_weapon_ep_cost(w_name: str) -> int:
    return WEAPONS.get(w_name, {}).get("ep_cost", 1)

def get_armour_def(a_name: str) -> int:
    ARMOURS = {
        "Plate Armor": 20,
        "Chainmail": 10,
        "Iron Armor": 10,
        "Leather Armor": 5
    }
    if a_name in ARMOURS:
        return ARMOURS[a_name]
    for grade_name, spec in ARMOUR_GRADES.items():
        if grade_name.lower() in a_name.lower():
            return spec.get("estimated_def_bonus", 0)
    return 0

def get_target_priorities(view: dict, self_bot_name: str) -> list:
    priorities = []
    if not isinstance(view, dict):
        return priorities
    current_region = view.get("currentRegion", {})
    if not isinstance(current_region, dict):
        return priorities
    detailed = get_detailed_enemy_stats(view, self_bot_name)
    players = detailed.get("players", [])
    monsters = detailed.get("monsters", [])
    self_data = view.get("self", {}) if isinstance(view, dict) else {}
    curr_hp = self_data.get("hp", 100) if isinstance(self_data, dict) else 100
    curr_ep = self_data.get("ep", 10) if isinstance(self_data, dict) else 10
    curr_atk = self_data.get("atk", 25) if isinstance(self_data, dict) else 25
    eq_weapon = self_data.get("equippedWeapon") if isinstance(self_data, dict) else None
    curr_weapon_name = eq_weapon.get("name", "Fist") if isinstance(eq_weapon, dict) else "Fist"
    w_range = WEAPONS.get(curr_weapon_name, {}).get("range", 0)
    w_ep_cost = WEAPONS.get(curr_weapon_name, {}).get("ep_cost", 1)

    current_region = view.get("currentRegion", {})
    current_is_dz = is_dead_zone(current_region)
    is_emergency = curr_hp <= 30 or current_is_dz

    if is_emergency:
        can_attack = curr_ep >= w_ep_cost
    else:
        can_attack = curr_ep >= (w_ep_cost + 2)

    for p in players:
        layer = p.get("layer", -1)
        if layer == -1:
            continue
        score = 0.0
        hp = p.get("hp", 100)
        
        target_weapon = p.get("weapon", "None")
        target_armor = p.get("armour", "None")
        target_ep = p.get("ep", 10)
        
        target_def = p.get("def", 5)
        target_total_def = max(target_def, get_armour_def(target_armor))
        net_atk = max(1, curr_atk - target_total_def)
        
        target_w_ep_cost = get_weapon_ep_cost(target_weapon)
        can_target_counter = target_ep >= target_w_ep_cost

        if not can_attack:
            score = 0.0
        elif layer <= w_range:
            if net_atk >= hp:
                score = 0.99
            elif hp <= 30:
                score = 0.98
            elif hp <= 60:
                score = 0.85
            else:
                score = 0.70

            if not can_target_counter:
                score = min(0.95, score + 0.10)

            score -= (target_total_def * 0.005)

            if net_atk <= 5:
                score *= 0.20
        else:
            score = 0.0
        priorities.append({
            "type": "player",
            "name": p.get("name"),
            "hp": hp,
            "atk": p.get("atk", 25),
            "def": target_total_def,
            "layer": layer,
            "region_id": p.get("region_id"),
            "score": max(0.0, score)
        })
    for m in monsters:
        layer = m.get("layer", -1)
        if layer == -1:
            continue
        score = 0.0
        hp = m.get("hp", 25)
        is_guardian = m.get("is_guardian", False)
        target_def = m.get("def", 1)
        net_atk = curr_atk - target_def
        if not can_attack:
            score = 0.0
        elif layer <= w_range:
            if net_atk >= hp:
                score = 0.99
            elif is_guardian:
                if hp <= 40:
                    score = 0.70
                else:
                    score = 0.10
            else:
                if hp <= 15:
                    score = 0.95
                else:
                    score = 0.80

            score -= (target_def * 0.005)

            if net_atk <= 5:
                score *= 0.20
        else:
            score = 0.0
        priorities.append({
            "type": "monster",
            "name": m.get("type"),
            "hp": hp,
            "atk": m.get("atk", 15),
            "def": target_def,
            "layer": layer,
            "region_id": m.get("region_id"),
            "score": max(0.0, score)
        })
    priorities.sort(key=lambda x: x["score"], reverse=True)
    return priorities