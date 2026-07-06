def parse_zone_status(agent_view_data):
    view = agent_view_data.get("view", {})
    current_region = view.get("currentRegion", {})
    current_region_id = current_region.get("id")
    
    visible_regions = view.get("visibleRegions", [])
    my_region_data = next((r for r in visible_regions if r.get("id") == current_region_id), {})
    
    location = current_region.get("name", "Unknown")
    terrain = current_region.get("terrain", my_region_data.get("terrain", "plains"))
    weather = view.get("weather", current_region.get("weather", "clear"))
    vision_modifier = my_region_data.get("visionModifier", 0)
    
    interactables = current_region.get("interactables", [])
    facility_names = [fac.get("name", "Unknown Facility") for fac in interactables]
    
    connections = current_region.get("connections", [])
    
    return {
        "location": location,
        "terrain": terrain,
        "weather": weather,
        "vision_modifier": vision_modifier,
        "facilities": facility_names,
        "links_count": len(connections)
    }