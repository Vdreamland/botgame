from game_data.world_info import DEATH_ZONE
from ai.Strategy.memory import mark_dead_zone

def is_dead_zone(region: dict) -> bool:
    if not isinstance(region, dict):
        return False
    active_dz = any([
        bool(region.get("isDeathZone")),
        bool(region.get("is_death_zone")),
        bool(region.get("isDeadZone")),
        bool(region.get("is_dead_zone")),
    ])
    if active_dz:
        r_id = region.get("id") or region.get("regionId") or region.get("region_id")
        r_name = region.get("name")
        if r_id and r_name:
            mark_dead_zone(r_id, r_name)
    return active_dz

def is_pending_dead_zone(region_id: str, view: dict) -> bool:
    if not isinstance(view, dict):
        return False
    pending = view.get("pendingDeathzones", []) or view.get("pending_death_zones", []) or view.get("pending_dead_zones", []) or view.get("pendingDeadZones", [])
    if isinstance(pending, list):
        for r in pending:
            if isinstance(r, dict):
                r_id = r.get("id") or r.get("regionId") or r.get("region_id")
                r_name = r.get("name")
                if r_id == region_id:
                    if r_id and r_name:
                        mark_dead_zone(r_id, r_name)
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
    pending = view.get("pendingDeathzones", []) or view.get("pending_death_zones", []) or view.get("pending_dead_zones", []) or view.get("pendingDeadZones", [])
    if isinstance(pending, list):
        for r in pending:
            if isinstance(r, dict):
                r_id = r.get("id") or r.get("regionId") or r.get("region_id")
                r_name = r.get("name")
                if r_id and r_name:
                    mark_dead_zone(r_id, r_name)
                    if r_id not in analysis["pending_dead_zones"]:
                        analysis["pending_dead_zones"].append(r_id)
            elif isinstance(r, str):
                mark_dead_zone(r, r)
                if r not in analysis["pending_dead_zones"]:
                    analysis["pending_dead_zones"].append(r)
    active = view.get("deathZones", []) or view.get("deathzones", []) or view.get("activeDeathzones", []) or view.get("active_death_zones", []) or view.get("dead_zones", [])
    if isinstance(active, list):
        for r in active:
            if isinstance(r, dict):
                r_id = r.get("id") or r.get("regionId") or r.get("region_id")
                r_name = r.get("name")
                if r_id and r_name:
                    mark_dead_zone(r_id, r_name)
                    if r_id not in analysis["dead_zones"]:
                        analysis["dead_zones"].append(r_id)
            elif isinstance(r, str):
                mark_dead_zone(r, r)
                if r not in analysis["dead_zones"]:
                    analysis["dead_zones"].append(r)
    regions = view.get("regions", {})
    if isinstance(regions, dict):
        for r_id, r_data in regions.items():
            if isinstance(r_data, dict):
                if is_dead_zone(r_data):
                    if r_id not in analysis["dead_zones"]:
                        analysis["dead_zones"].append(r_id)
                elif is_pending_dead_zone(r_id, view):
                    if r_id not in analysis["pending_dead_zones"]:
                        analysis["pending_dead_zones"].append(r_id)
                else:
                    if r_id not in analysis["safe_zones"] and r_id not in analysis["dead_zones"] and r_id not in analysis["pending_dead_zones"]:
                        analysis["safe_zones"].append(r_id)
    return analysis

def get_damage_per_second() -> float:
    return float(DEATH_ZONE.get("damage_per_second", 1.34))

def is_interact_restricted() -> bool:
    return not bool(DEATH_ZONE.get("action_restrictions", {}).get("interact", True))