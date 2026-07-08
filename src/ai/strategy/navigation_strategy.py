import os
from src.utils.zone_helper import get_adjacent_safe_zones, find_shortest_path, calculate_region_distances
from src.game_data import GLOBAL_MAP

def get_ally_names(my_name):
    allies = set()
    for key, value in os.environ.items():
        if key.startswith("BOT") and key.endswith("_NAME"):
            if value and value != my_name:
                allies.add(value)
    return allies

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
        
        visible_regions = view.get("visibleRegions", [])
        region_map = {r.get("id"): r for r in visible_regions if r.get("id")}
        if current_region_id not in region_map:
            region_map[current_region_id] = current_region
        
        dead_ids = {r.get("id") for r in visible_regions if r.get("id") and r.get("isDeathZone")}
        unsafe_regions = gas_ids.union(dead_ids)
        
        if current_region.get("isDeathZone"):
            safe_targets = get_adjacent_safe_zones(connections, gas_ids)
            safe_targets = [rid for rid in safe_targets if not region_map.get(rid, {}).get("isDeathZone")]
            if safe_targets:
                return 100, {"action_type": "move", "destination": safe_targets[0]}
            return 100, {"action_type": "move", "destination": connections[0]}
        
        elif current_region_id in gas_ids:
            safe_targets = get_adjacent_safe_zones(connections, gas_ids)
            safe_targets = [rid for rid in safe_targets if not region_map.get(rid, {}).get("isDeathZone")]
            if safe_targets:
                return 91, {"action_type": "move", "destination": safe_targets[0]}
            return 91, {"action_type": "move", "destination": connections[0]}
        
        visible_agents = view.get("visibleAgents", [])
        visible_monsters = view.get("visibleMonsters", [])
        
        self_data = view.get("self", {})
        my_id = self_data.get("id")
        my_ep = self_data.get("ep", 10)
        my_hp = self_data.get("hp", 100)
        my_name = self_data.get("name", "Unknown")
        equipped_weapon = self_data.get("equippedWeapon")
        eq_weapon_name = equipped_weapon.get("name") if isinstance(equipped_weapon, dict) else (equipped_weapon if equipped_weapon else "None")
        has_weapon = (eq_weapon_name not in ["None", "Fist"])
        
        ally_names = get_ally_names(my_name)
        
        if has_weapon and my_ep >= 4:
            for agent in visible_agents:
                if agent.get("isAlive", True):
                    region_id = agent.get("regionId")
                    if region_id and region_id in connections:
                        agent_name = agent.get("name")
                        if agent_name and agent_name not in ally_names:
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
        
        all_connections = dict(GLOBAL_MAP)
        if hasattr(manager, "accumulated_connections"):
            all_connections.update(manager.accumulated_connections)
        
        if hasattr(manager, "pending_loot_regions") and manager.pending_loot_regions:
            target_loot_region = manager.pending_loot_regions[0]
            
            safe_connections = {}
            for r_id, conns in all_connections.items():
                safe_connections[r_id] = [c for c in conns if c not in unsafe_regions]
            
            path = find_shortest_path(current_region_id, target_loot_region, safe_connections)
            if len(path) > 1:
                loot_score = 95 if my_hp >= 60 else 84
                return loot_score, {"action_type": "move", "destination": path[1]}
        
        distances = calculate_region_distances(current_region, visible_regions)
        safe_regions = [
            r_id for r_id, dist in distances.items()
            if r_id and r_id not in gas_ids and not region_map.get(r_id, {}).get("isDeathZone")
        ]
        
        safe_neighbors = [rid for rid in connections if rid and rid not in gas_ids and not region_map.get(rid, {}).get("isDeathZone")]
        if not safe_neighbors:
            return 50, {"action_type": "move", "destination": connections[0]}
        
        best_neighbor = None
        best_neighbor_score = -999
        
        game_id = getattr(manager, "game_id", None)
        team_states = manager.memory.get_team_states(current_game_id=game_id) if hasattr(manager, "memory") else {}
        teammate_regions = []
        is_leader = True
        
        for teammate, state in team_states.items():
            if teammate != my_name:
                if teammate < my_name:
                    is_leader = False
                t_reg_id = state.get("region_id")
                if t_reg_id:
                    teammate_regions.append(t_reg_id)
        
        path_to_teammate = []
        if teammate_regions and not is_leader:
            target_teammate_region = teammate_regions[0]
            path_to_teammate = find_shortest_path(current_region_id, target_teammate_region, all_connections)
        
        has_layer_0_enemies = getattr(manager, "has_layer_0_enemies", False)
        
        visible_ruins = view.get("visibleRuins", [])
        active_ruin_ids = {r.get("ruinId") for r in visible_ruins if r.get("ruinId") and not r.get("isEmpty", False)}
        
        for rid in safe_neighbors:
            score = 50
            r_data = region_map.get(rid, {})
            
            visited_history = manager.memory.visited_history if hasattr(manager, "memory") else []
            if rid in visited_history:
                idx = len(visited_history) - 1 - visited_history.index(rid)
                if idx == 0:
                    score -= 30
                elif idx == 1:
                    score -= 20
                elif idx == 2:
                    score -= 10
            
            if r_data.get("items"):
                score += 20
            
            facilities = r_data.get("interactables", [])
            for fac in facilities:
                fac_name = fac.get("name")
                if fac_name in ["Supply Cache", "Medical Facility"]:
                    fac_key = f"{rid}_{fac_name}"
                    if not hasattr(manager, "interacted_facilities") or fac_key not in manager.interacted_facilities:
                        score += 15
            
            if r_data.get("terrain", "").lower() == "ruins":
                score += 10
                
            if rid in active_ruin_ids:
                score += 30
            
            if path_to_teammate and len(path_to_teammate) > 1:
                if rid == path_to_teammate[1]:
                    score += 25
            
            if has_layer_0_enemies:
                has_melee_enemy_at_layer_0 = False
                for agent in visible_agents:
                    if agent.get("id") != my_id and agent.get("regionId") == current_region_id and agent.get("isAlive", True):
                        if agent.get("name") not in ally_names:
                            e_weapon = agent.get("weapon", "None")
                            if e_weapon in ["None", "Fist", "Dagger", "Sword", "Katana"]:
                                has_melee_enemy_at_layer_0 = True
                                break
                if not has_melee_enemy_at_layer_0:
                    for monster in visible_monsters:
                        if monster.get("regionId") == current_region_id and monster.get("isAlive", True):
                            has_melee_enemy_at_layer_0 = True
                            break
                if has_melee_enemy_at_layer_0 and eq_weapon_name in ["Bow", "Pistol", "Sniper rifle"]:
                    score += 45
            
            if score > best_neighbor_score:
                best_neighbor_score = score
                best_neighbor = rid
        
        if best_neighbor:
            return 55, {"action_type": "move", "destination": best_neighbor}
        
        return 0, None