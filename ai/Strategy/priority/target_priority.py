from ai.detector.enemy_detector import get_detailed_enemy_stats
from game_data.weapon_info import WEAPONS

def get_target_priorities(view: dict, self_bot_name: str) -> list:
    priorities = []
    if not isinstance(view, dict):
        return priorities
    detailed = get_detailed_enemy_stats(view, self_bot_name)
    players = detailed.get("players", [])
    monsters = detailed.get("monsters", [])
    self_data = view.get("self", {}) if isinstance(view, dict) else {}
    curr_ep = self_data.get("ep", 10) if isinstance(self_data, dict) else 10
    eq_weapon = self_data.get("equippedWeapon") if isinstance(self_data, dict) else None
    curr_weapon_name = eq_weapon.get("name", "Fist") if isinstance(eq_weapon, dict) else "Fist"
    w_range = WEAPONS.get(curr_weapon_name, {}).get("range", 0)
    w_ep_cost = WEAPONS.get(curr_weapon_name, {}).get("ep_cost", 1)
    can_attack = curr_ep >= w_ep_cost
    for p in players:
        layer = p.get("layer", -1)
        if layer == -1:
            continue
        score = 0.0
        hp = p.get("hp", 100)
        if not can_attack:
            score = 0.0
        elif layer <= w_range:
            if hp <= 30:
                score = 0.98
            elif hp <= 60:
                score = 0.85
            else:
                score = 0.70
        else:
            score = 0.0
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
        if not can_attack:
            score = 0.0
        elif layer <= w_range:
            if is_guardian:
                if hp <= 40:
                    score = 0.70
                else:
                    score = 0.10
            else:
                if hp <= 15:
                    score = 0.95
                else:
                    score = 0.80
        else:
            score = 0.0
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