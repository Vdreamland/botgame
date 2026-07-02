from ai.detector.enemy_detector import get_detailed_enemy_stats
from game_data.weapon_info import WEAPONS

def get_target_priorities(view: dict, self_bot_name: str) -> list:
    priorities = []
    if not isinstance(view, dict):
        return priorities
    detailed = get_detailed_enemy_stats(view, self_bot_name)
    players = detailed.get("players", [])
    monsters = detailed.get("monsters", [])
    eq_weapon = view.get("equippedWeapon")
    curr_weapon_name = eq_weapon.get("name", "Fist") if isinstance(eq_weapon, dict) else "Fist"
    w_range = WEAPONS.get(curr_weapon_name, {}).get("range", 0)
    for p in players:
        layer = p.get("layer", -1)
        if layer == -1:
            continue
        score = 0.0
        hp = p.get("hp", 100)
        if layer <= w_range:
            if hp <= 30:
                score = 0.98
            elif hp <= 60:
                score = 0.85
            else:
                score = 0.70
        else:
            score = 0.30 - (layer * 0.05)
        priorities.append({
            "type": "player",
            "name": p.get("name"),
            "hp": hp,
            "atk": p.get("atk", 25),
            "def": p.get("def", 5),
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
        if layer <= w_range:
            if is_guardian:
                if hp <= 50:
                    score = 0.75
                else:
                    score = 0.40
            else:
                if hp <= 15:
                    score = 0.95
                else:
                    score = 0.80
        else:
            if is_guardian:
                score = 0.15 - (layer * 0.03)
            else:
                score = 0.50 - (layer * 0.10)
        priorities.append({
            "type": "monster",
            "name": m.get("type"),
            "hp": hp,
            "atk": m.get("atk", 15),
            "def": m.get("def", 1),
            "layer": layer,
            "region_id": m.get("region_id"),
            "score": max(0.0, score)
        })
    priorities.sort(key=lambda x: x["score"], reverse=True)
    return priorities