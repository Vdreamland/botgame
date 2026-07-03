from ai.detector.self_detector import get_self_vital_status
from ai.detector.zone_detector import detect_facility_detail
from ai.detector.dead_zone_detector import is_dead_zone

def get_interact_priorities(view: dict) -> list:
    priorities = []
    if not isinstance(view, dict):
        return priorities
    current_region = view.get("currentRegion", {})
    if not isinstance(current_region, dict):
        return priorities
    if is_dead_zone(current_region):
        return priorities
    
    is_used = current_region.get("facilityUsed", current_region.get("isUsed", False))
    if is_used:
        return priorities

    detail = detect_facility_detail(current_region)
    if not detail:
        return priorities
    facility = detail["name"]
    vital = get_self_vital_status(view)
    hp = vital.get("hp", 100)
    score = 0.0
    if facility == "Medical Facility":
        if hp <= 40:
            score = 0.96
        elif hp <= 80:
            score = 0.70
        else:
            score = 0.0
    elif facility == "Supply Cache":
        score = 0.93
    elif facility == "Watchtower":
        score = 0.80
    elif facility == "Broadcast Station":
        score = 0.15
    if score > 0.0:
        priorities.append({
            "id": detail["id"],
            "name": facility,
            "score": score
        })
    return priorities