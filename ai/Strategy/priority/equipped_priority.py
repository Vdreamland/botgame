from ai.detector.self_detector import check_better_equipments_in_inventory
from game_data.weapon_info import WEAPONS
from game_data.armour_info import ARMOUR_GRADES

def get_equipment_priorities(view: dict) -> list:
    priorities = []
    if not isinstance(view, dict):
        return priorities
    inventory = view.get("inventory", [])
    if not isinstance(inventory, list) or not inventory:
        return priorities
    better = check_better_equipments_in_inventory(view)
    for item in inventory:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        item_id = item.get("id")
        i_type = item.get("type", "").lower()
        if not name or not item_id:
            continue
        score = 0.0
        if (i_type == "weapon" or name in WEAPONS) and better.get("better_weapon_found"):
            if name == better.get("best_weapon_name"):
                score = 0.95
            else:
                score = 0.20
        elif (i_type == "armour" or "armor" in i_type or any(g in name for g in ARMOUR_GRADES)) and better.get("better_armour_found"):
            if name == better.get("best_armour_name"):
                score = 0.90
            else:
                score = 0.15
        if score > 0.0:
            priorities.append({
                "id": item_id,
                "name": name,
                "type": "weapon" if (i_type == "weapon" or name in WEAPONS) else "armour",
                "score": score
            })
    priorities.sort(key=lambda x: x["score"], reverse=True)
    return priorities