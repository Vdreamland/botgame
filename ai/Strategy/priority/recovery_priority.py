from ai.detector.self_detector import get_self_vital_status
from game_data.item_info import RECOVERY_ITEMS

def get_recovery_priorities(view: dict) -> list:
    priorities = []
    if not isinstance(view, dict):
        return priorities
    inventory = view.get("inventory", [])
    if not isinstance(inventory, list) or not inventory:
        return priorities
    vital = get_self_vital_status(view)
    hp = vital.get("hp", 100)
    max_hp = vital.get("max_hp", 100)
    ep = vital.get("ep", 10)
    max_ep = vital.get("max_ep", 10)
    hp_diff = max_hp - hp
    ep_diff = max_ep - ep
    for item in inventory:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        item_id = item.get("id")
        if not name or not item_id or name not in RECOVERY_ITEMS:
            continue
        score = 0.0
        if name == "Medkit":
            if hp <= 30 and hp_diff >= 30:
                score = 0.98
            elif hp_diff >= 30 and ep_diff >= 5:
                score = 0.85
            elif hp_diff >= 30 or ep_diff >= 5:
                score = 0.70
            else:
                score = 0.10
        elif name == "Emergency Food":
            if hp <= 40 and hp_diff >= 20:
                score = 0.90
            elif hp_diff >= 20:
                score = 0.75
            else:
                score = 0.15
        elif name == "Bandage":
            if hp <= 60 and hp_diff >= 10:
                score = 0.80
            elif hp_diff >= 10:
                score = 0.60
            else:
                score = 0.10
        elif name == "Energy Drink":
            if ep <= 2 and ep_diff >= 5:
                score = 0.95
            elif ep_diff >= 5:
                score = 0.80
            else:
                score = 0.15
        if score > 0.0:
            priorities.append({
                "id": item_id,
                "name": name,
                "score": score
            })
    priorities.sort(key=lambda x: x["score"], reverse=True)
    return priorities