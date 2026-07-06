from collections import deque
from src.game_data import TERRAINS, WEATHERS

def get_adjacent_safe_zones(current_links, gas_zones):
    safe_zones = []
    for link in current_links:
        if link not in gas_zones:
            safe_zones.append(link)
    return safe_zones

def find_shortest_path(start_region, target_region, map_connections):
    if start_region == target_region:
        return [start_region]
    
    queue = deque([[start_region]])
    visited = {start_region}
    
    while queue:
        path = queue.popleft()
        node = path[-1]
        
        neighbors = map_connections.get(node, [])
        for neighbor in neighbors:
            if neighbor == target_region:
                return path + [neighbor]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + [neighbor])
    return []

def get_terrain_penalty(terrain_type, weather_type):
    terrain_data = TERRAINS.get(terrain_type, {"vision_mod": 0, "ep_cost_mod": 0})
    weather_data = WEATHERS.get(weather_type, {"vision_mod": 0})
    
    total_vision_mod = terrain_data.get("vision_mod", 0) + weather_data.get("vision_mod", 0)
    total_ep_cost_mod = terrain_data.get("ep_cost_mod", 0)
    
    return {
        "vision_modifier": total_vision_mod,
        "ep_cost_modifier": total_ep_cost_mod
    }

def calculate_region_distances(current_region_id, visible_regions):
    if not current_region_id:
        return {}
        
    region_map = {r.get("id"): r for r in visible_regions if r.get("id")}
    
    distances = {current_region_id: 0}
    queue = deque([current_region_id])
    
    while queue:
        curr = queue.popleft()
        curr_dist = distances[curr]
        region_data = region_map.get(curr, {})
        for conn in region_data.get("connections", []):
            if conn in region_map and conn not in distances:
                distances[conn] = curr_dist + 1
                queue.append(conn)
                
    return distances