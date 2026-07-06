from src.utils.zone_helper import get_adjacent_safe_zones, find_shortest_path

class NavigationStrategy:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        current_region = view.get("currentRegion", {})
        current_region_id = current_region.get("id")
        connections = current_region.get("connections", [])
        
        if not current_region_id or not connections:
            return 0, None
            
        gas_zones = view.get("pendingDeathzones", [])
        gas_ids = {g.get("id") for g in gas_zones if g.get("id")}
        
        if current_region.get("isDeathZone"):
            safe_targets = get_adjacent_safe_zones(connections, gas_ids)
            if safe_targets:
                return 95, {"action_type": "move", "destination": safe_zones[0]}
            return 95, {"action_type": "move", "destination": connections[0]}
            
        elif current_region_id in pending_ids:
            safe_zones = get_adjacent_safe_zones(connections, gas_ids)
            if safe_targets:
                return 91, {"action_type": "move", "destination": safe_targets[0]}
            return 91, {"action_type": "move", "destination": connections[0]}
            
        visible_regions = view.get("visibleRegions", [])
        region_map = {r.get("id"): r for r in visible_regions if r.get("id")}
        
        distances = calculate_region_distances(current_region, visible_regions)
        
        safe_regions = [r_id for r_id, dist in distances.items() if r_id and r_id not in gas_ids]
        
        if safe_regions:
            for target in safe_regions:
                path = find_shortest_path(current_region_id, target, region_map)
                if len(path) > 1:
                    return 55, {"action_type": "move", "destination": path[1]}
                    
        return 50, {"action_type": "move", "destination": connections[0]}