from ai.detector.zone_detector import detect_terrain
from ai.detector.dead_zone_detector import get_damage_per_second, is_dead_zone, is_pending_dead_zone
from ai.detector.ruin_detector import get_visible_ruins_status
from ai.Strategy.memory import get_all_known_dead_zones, is_visited, get_visit_count

def get_navigation_priorities(view: dict, self_bot_name: str) -> list:
    priorities = []
    if not isinstance(view, dict):
        return priorities

    self_data = view.get("self", {})
    hp = self_data.get("hp", 100)
    inventory = self_data.get("inventory", [])
    has_heal = False
    if isinstance(inventory, list):
        for item in inventory:
            if isinstance(item, dict) and item.get("name") in ("Medkit", "Emergency Food", "Bandage"):
                has_heal = True
                break

    occupied_regions = set()
    if hp < 40 and not has_heal:
        agents = view.get("visibleAgents", [])
        if isinstance(agents, list):
            for a in agents:
                if isinstance(a, dict) and a.get("name") != self_bot_name:
                    r_id = a.get("regionId") or a.get("region")
                    if r_id:
                        occupied_regions.add(r_id)
        monsters = view.get("visibleMonsters", [])
        if isinstance(monsters, list):
            for m in monsters:
                if isinstance(m, dict):
                    r_id = m.get("regionId") or m.get("region")
                    if r_id:
                        occupied_regions.add(r_id)

    current_region = view.get("currentRegion", {})
    if not isinstance(current_region, dict):
        return priorities
    connections = current_region.get("connections", [])
    if not isinstance(connections, list):
        return priorities
    regions = view.get("regions", {})

    for conn_id in connections:
        r_data = regions.get(conn_id, {}) if isinstance(regions, dict) else {}
        name = r_data.get("name", "Unknown")
        score = 0.50
        terrain = detect_terrain(r_data)
        if terrain == "ruins":
            ruins_status = get_visible_ruins_status(view)
            if conn_id in ruins_status:
                gauge = ruins_status[conn_id].get("gauge", 0)
                max_g = ruins_status[conn_id].get("maxGauge", 3)
                if gauge < max_g:
                    score += 0.20
                else:
                    score += 0.10
        elif terrain in ("forest", "hills", "water"):
            score += 0.05
        if is_dead_zone(r_data):
            score = 0.0
        elif is_pending_dead_zone(conn_id, view):
            score = 0.02
        visit_count = get_visit_count(conn_id)
        if visit_count > 0:
            score -= (visit_count * 0.15)
        if conn_id in occupied_regions:
            score = 0.0
        priorities.append({
            "id": conn_id,
            "name": name,
            "score": max(0.0, min(1.0, score))
        })
    priorities.sort(key=lambda x: x["score"], reverse=True)
    return priorities