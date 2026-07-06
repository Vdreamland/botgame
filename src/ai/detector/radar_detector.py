from src.utils import calculate_region_distances

def parse_radar_status(agent_view_data):
    view = agent_view_data.get("view", {})
    current_region = view.get("currentRegion", {})
    current_region_id = current_region.get("id")
    
    visible_regions = view.get("visibleRegions", [])
    region_map = {r.get("id"): r for r in visible_regions if r.get("id")}
    
    if current_region_id not in region_map and current_region_id:
        region_map[current_region_id] = current_region
        
    distances = calculate_region_distances(current_region, visible_regions)
    
    layers = {i: [] for i in range(1, 4)}
    max_layer = 0
    
    for r_id, dist in distances.items():
        if dist == 0:
            continue
        if dist in layers:
            r_data = region_map.get(r_id, {})
            name = r_data.get("name", "Unknown")
            layers[dist].append(name)
            if dist > max_layer:
                max_layer = dist
                
    return {
        "layers": layers,
        "max_detected_layer": max_layer
    }