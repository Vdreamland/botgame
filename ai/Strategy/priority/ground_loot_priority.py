from ai.detector.ground_detector import detect_ground_loot
from ai.detector.self_detector import get_self_vital_status, check_inventory_full
from game_data.weapon_info import WEAPONS
from game_data.armour_info import ARMOUR_GRADES
from game_data.item_info import RECOVERY_ITEMS

def get_ground_loot_priorities(view: dict) -> list:
    priorities = []
    if not isinstance(view, dict):
        return priorities
    current_region = view.get("currentRegion", {})
    if not isinstance(current_region, dict):
        return priorities
    items = current_region.get("items", [])
    if not isinstance(items, list) or not items:
        return priorities
    is_full = check_inventory_full(view)
    vital = get_self_vital_status(view)
    hp = vital.get("hp", 100)
    max_hp = vital.get("max_hp", 100)
    ep = vital.get("ep", 10)
    max_ep = vital.get("max_ep", 10)
    self_data = view.get("self", {})
    curr_weapon_name = "None"
    curr_weapon_bonus = 0
    curr_armour_name = "None"
    curr_armour_bonus = 0
    if isinstance(self_data, dict):
        eq_weapon = self_data.get("equippedWeapon")
        curr_weapon_name = eq_weapon.get("name", "Fist") if isinstance(eq_weapon, dict) else "Fist"
        curr_weapon_bonus = WEAPONS.get(curr_weapon_name, {}).get("atk_bonus", 0)
        eq_armour = self_data.get("equippedArmor")
        curr_armour_name = eq_armour.get("name", "None") if isinstance(eq_armour, dict) else "None"
        if curr_armour_name != "None":
            for grade, spec in ARMOUR_GRADES.items():
                if grade.lower() in curr_armour_name.lower():
                    curr_armour_bonus = spec.get("estimated_def_bonus", 0)
                    break
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        item_id = item.get("id")
        i_type = item.get("type", "").lower()
        if not name or not item_id:
            continue
        score = 0.0
        if name == "sMoltz":
            score = 0.99
        elif is_full:
            score = 0.0
        elif i_type == "weapon" or name in WEAPONS:
            bonus = WEAPONS.get(name, {}).get("atk_bonus", 0)
            if curr_weapon_name == "Fist":
                score = 0.95
            elif bonus > curr_weapon_bonus:
                score = 0.85
            else:
                score = 0.10
        elif i_type == "armour" or "armor" in i_type or any(g in name for g in ARMOUR_GRADES):
            item_bonus = 0
            for grade, spec in ARMOUR_GRADES.items():
                if grade.lower() in name.lower():
                    item_bonus = spec.get("estimated_def_bonus", 0)
                    break
            if curr_armour_name == "None":
                score = 0.90
            elif item_bonus > curr_armour_bonus:
                score = 0.80
            else:
                score = 0.05
        elif name in RECOVERY_ITEMS:
            hp_diff = max_hp - hp
            ep_diff = max_ep - ep
            if name in ("Medkit", "Emergency Food", "Bandage") and hp_diff > 0:
                if hp <= 30:
                    score = 0.92
                elif hp <= 60:
                    score = 0.75
                else:
                    score = 0.70
            elif name == "Energy Drink" and ep_diff > 0:
                if ep <= 2:
                    score = 0.85
                elif ep <= 5:
                    score = 0.65
                else:
                    score = 0.60
            else:
                score = 0.70
        else:
            score = 0.15
        priorities.append({
            "id": item_id,
            "name": name,
            "score": score
        })
    priorities.sort(key=lambda x: x["score"], reverse=True)
    return priorities