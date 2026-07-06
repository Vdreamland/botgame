from collections import deque

def parse_radar_status(agent_view_data):
    view = agent_view_data.get("view", {})
    current_region = view.get("currentRegion", {})
    current_id = current_region.get("id")
    
    visible_regions = view.get("visibleRegions", [])
    regions_map = {r.get("id"): r for r in visible_regions}
    
    if current_id not in regions_map and current_id:
        regions_map[current_id] = current_region
        
    queue = deque([(current_id, 0)])
    visited = {current_id: 0}
    
    while queue:
        node_id, dist = queue.popleft()
        node_data = regions_map.get(node_id)
        if not node_data:
            continue
            
        for neighbor_id in node_data.get("connections", []):
            if neighbor_id not in visited and neighbor_id in regions_map:
                visited[neighbor_id] = dist + 1
                queue.append((neighbor_id, dist + 1))
                
    layers = {}
    for r_id, dist in visited.items():
        r_data = regions_map.get(r_id, {})
        r_name = r_data.get("name", "Unknown")
        
        if dist not in layers:
            layers[dist] = []
        layers[dist].append(r_name)
        
    return {
        "layers": layers,
        "max_detected_layer": max(layers.keys()) if layers else 0
    }