from src.utils.zone_helper import get_adjacent_safe_zones, find_shortest_path, calculate_region_distances

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
        
        visible_agents = view.get("visibleAgents", [])
        visible_monsters = view.get("visibleMonsters", [])
        
        for agent in visible_agents:
            if agent.get("isAlive", True):
                region_id = agent.get("regionId")
                if region_id and region_id in connections:
                    hp_val = agent.get("hp", 100)
                    max_hp_val = agent.get("maxHp", 100)
                    hp_ratio = hp_val / max_hp_val if max_hp_val > 0 else 1.0
                    if hp_ratio < 0.3:
                        return 94, {"action_type": "move", "destination": region_id}
                        
        for monster in visible_monsters:
            if monster.get("isAlive", True):
                region_id = monster.get("regionId")
                if region_id and region_id in connections:
                    hp_val = monster.get("hp", 100)
                    max_hp_val = monster.get("maxHp", 100)
                    hp_ratio = hp_val / max_hp_val if max_hp_val > 0 else 1.0
                    if hp_ratio < 0.3:
                        return 94, {"action_type": "move", "destination": region_id}
                        
        if current_region.get("isDeathZone"):
            safe_targets = get_adjacent_safe_zones(connections, gas_ids)
            if safe_targets:
                return 95, {"action_type": "move", "destination": safe_targets[0]}
            return 95, {"action_type": "move", "destination": connections[0]}
            
        elif current_region_id in gas_ids:
            safe_targets = get_adjacent_safe_zones(connections, gas_ids)
            if safe_targets:
                return 91, {"action_type": "move", "destination": safe_targets[0]}
            return 91, {"action_type": "move", "destination": connections[0]}
            
        visible_regions = view.get("visibleRegions", [])
        all_connections = {r.get("id"): r.get("connections", []) for r in visible_regions if r.get("id")}
        if current_region_id not in all_connections:
            all_connections[current_region_id] = connections
            
        if hasattr(manager, "pending_loot_regions") and manager.pending_loot_regions:
            target_loot_region = manager.pending_loot_regions[0]
            path = find_shortest_path(current_region_id, target_loot_region, all_connections)
            if len(path) > 1:
                return 84, {"action_type": "move", "destination": path[1]}
                
        distances = calculate_region_distances(current_region, visible_regions)
        safe_regions = [r_id for r_id, dist in distances.items() if r_id and r_id not in gas_ids]
        
        if safe_regions:
            for target in safe_regions:
                path = find_shortest_path(current_region_id, target, all_connections)
                if len(path) > 1:
                    return 55, {"action_type": "move", "destination": path[1]}
                    
        return 50, {"action_type": "move", "destination": connections[0]}