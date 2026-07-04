def detect_terrain(region: dict) -> str:
    if not isinstance(region, dict):
        return "Unknown"
    return region.get("terrain", "Plains")

def detect_weather(view: dict) -> str:
    if not isinstance(view, dict):
        return "Clear"
    weather = view.get("weather")
    if not weather:
        current_region = view.get("currentRegion", {})
        if isinstance(current_region, dict):
            weather = current_region.get("weather")
    return weather if weather else "Clear"

def detect_facility_detail(region: dict) -> dict:
    if not isinstance(region, dict):
        return None
        
    facility_data = region.get("facility")
    if isinstance(facility_data, dict) and facility_data:
        return {
            "id": facility_data.get("id") or facility_data.get("name"),
            "name": facility_data.get("name")
        }
    
    items = region.get("items", [])
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                item_name = item.get("name", "")
                item_type = str(item.get("type", "")).lower()
                if item_type == "facility" or item_name in ("Medical Facility", "Supply Cache", "Watchtower", "Broadcast Station", "Cave Entrance"):
                    return {
                        "id": item.get("id") or item.get("name"),
                        "name": item_name
                    }
            elif isinstance(item, str):
                if item in ("Medical Facility", "Supply Cache", "Watchtower", "Broadcast Station", "Cave Entrance"):
                    return {
                        "id": item,
                        "name": item
                    }
    return None

def detect_facility(region: dict) -> str:
    detail = detect_facility_detail(region)
    if detail:
        return detail.get("name", "None")
    return "None"

def analyze_visible_world(view: dict) -> dict:
    return {}