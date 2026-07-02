from ai.detector.dead_zone_detector import analyze_death_zones, is_pending_dead_zone, is_dead_zone
from ai.detector.zone_detector import detect_terrain, detect_facility
from ai.detector.enemy_detector import get_visible_enemies_by_layer
from ai.Strategy.memory import get_visit_count, is_death_spot
from game_data.world_info import TERRAINS

def get_navigation_priorities(view: dict, self_bot_name: str) -> list:
    priorities = []
    if not isinstance(view, dict):
        return priorities
    current_region = view.get("currentRegion", {})
    if not isinstance(current_region, dict):
        return priorities
    connections = current_region.get("connections", [])
    if not isinstance(connections, list) or not connections:
        return priorities
    regions = view.get("regions", {})
    death_analysis = analyze_death_zones(view)
    layer_summary = get_visible_enemies_by_layer(view, self_bot_name)
    for conn_id in connections:
        r_data = regions.get(conn_id, {}) if isinstance(regions, dict) else {}
        score = 0.50
        name = r_data.get("name", str(conn_id))
        is_dz = is_dead_zone(r_data)
        is_pending = is_pending_dead_zone(conn_id, view)
        terrain = detect_terrain(r_data)
        facility = detect_facility(r_data)
        if is_dz:
            score = 0.0
        elif is_pending:
            score = 0.05
        else:
            if facility == "Medical Facility":
                self_data = view.get("self", {})
                hp = self_data.get("hp", 100)
                if hp <= 40:
                    score += 0.40
                elif hp <= 80:
                    score += 0.20
            elif facility == "Supply Cache":
                score += 0.25
            elif facility == "Watchtower":
                score += 0.15
            terrain_key = terrain.lower()
            extra_cost = TERRAINS.get(terrain_key, {}).get("extra_ep_cost", 0)
            score -= (extra_cost * 0.15)
            l1_counts = layer_summary.get(1, {})
            p_count = l1_counts.get("P", 0)
            m_count = l1_counts.get("M", 0)
            if p_count > 0:
                score -= (p_count * 0.10)
            if m_count > 0:
                score -= (m_count * 0.05)
            if is_death_spot(conn_id):
                score += 0.45
        visit_count = get_visit_count(conn_id)
        if visit_count > 0:
            score -= (visit_count * 0.15)
        priorities.append({
            "id": conn_id,
            "name": name,
            "score": max(0.0, min(1.0, score))
        })
    priorities.sort(key=lambda x: x["score"], reverse=True)
    return priorities