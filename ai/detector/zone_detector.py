from game_data.world_info import TERRAINS, WEATHERS, FACILITIES

def detect_terrain(region: dict) -> str:
    if not isinstance(region, dict):
        return "plains"
    terrain = region.get("terrain", "plains")
    if terrain not in TERRAINS:
        return "plains"
    return terrain

def detect_facility(region: dict) -> str:
    if not isinstance(region, dict):
        return None
    facility = region.get("facility")
    if facility in FACILITIES:
        is_used = bool(region.get("facilityUsed", region.get("isUsed", False)))
        if not is_used:
            return facility
    interactables = region.get("interactables", [])
    if isinstance(interactables, list):
        for item in interactables:
            if isinstance(item, dict):
                name = item.get("name")
                if name in FACILITIES:
                    is_used = bool(item.get("isUsed", item.get("used", False)))
                    if not is_used:
                        return name
    return None

def detect_weather(view: dict) -> str:
    if not isinstance(view, dict):
        return "clear"
    weather = view.get("weather")
    if not weather:
        current_region = view.get("currentRegion", {})
        if isinstance(current_region, dict):
            weather = current_region.get("weather")
    if weather in WEATHERS:
        return weather
    return "clear"

def analyze_visible_world(view: dict) -> dict:
    analysis = {
        "current_weather": "clear",
        "current_terrain": "plains",
        "current_facility": None,
        "visible_terrains": {t: [] for t in TERRAINS},
        "visible_facilities": [],
        "total_regions": 0
    }
    if not isinstance(view, dict):
        return analysis
    analysis["current_weather"] = detect_weather(view)
    current_region = view.get("currentRegion", {})
    if isinstance(current_region, dict):
        analysis["current_terrain"] = detect_terrain(current_region)
        analysis["current_facility"] = detect_facility(current_region)
    regions = view.get("regions", {})
    if isinstance(regions, dict):
        analysis["total_regions"] = len(regions)
        for r_id, r_data in regions.items():
            if isinstance(r_data, dict):
                terrain = detect_terrain(r_data)
                facility = detect_facility(r_data)
                if terrain in analysis["visible_terrains"]:
                    analysis["visible_terrains"][terrain].append(r_id)
                if facility:
                    analysis["visible_facilities"].append({
                        "region_id": r_id,
                        "facility_name": facility,
                        "is_used": r_data.get("facilityUsed", r_data.get("isUsed", False))
                    })
    return analysis