from game_data.world_info import DEATH_ZONE

def is_dead_zone(region: dict) -> bool:
    if not isinstance(region, dict):
        return False
    return bool(region.get("isDeathZone", False))

def is_pending_dead_zone(region_id: str, view: dict) -> bool:
    if not isinstance(view, dict):
        return False
    pending = view.get("pendingDeathzones", [])
    if isinstance(pending, list):
        for r in pending:
            if isinstance(r, dict) and r.get("id") == region_id:
                return True
            elif isinstance(r, str) and r == region_id:
                return True
    return False

def analyze_death_zones(view: dict) -> dict:
    analysis = {
        "current_is_dead_zone": False,
        "dead_zones": [],
        "pending_dead_zones": [],
        "safe_zones": []
    }
    if not isinstance(view, dict):
        return analysis
    current_region = view.get("currentRegion", {})
    if isinstance(current_region, dict):
        analysis["current_is_dead_zone"] = is_dead_zone(current_region)
    regions = view.get("regions", {})
    if isinstance(regions, dict):
        for r_id, r_data in regions.items():
            if isinstance(r_data, dict):
                if is_dead_zone(r_data):
                    analysis["dead_zones"].append(r_id)
                elif is_pending_dead_zone(r_id, view):
                    analysis["pending_dead_zones"].append(r_id)
                else:
                    analysis["safe_zones"].append(r_id)
    return analysis

def get_damage_per_second() -> float:
    return float(DEATH_ZONE.get("damage_per_second", 1.34))

def is_interact_restricted() -> bool:
    return not bool(DEATH_ZONE.get("action_restrictions", {}).get("interact", True))