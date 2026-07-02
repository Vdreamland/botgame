# utility/strategy/movement_solver.py

from utility.detector.layer_detector import calculate_distances
from game_data.world_info import TERRAINS

def evaluate_movement_routes(bot_name: str, self_data: dict, current_region: dict, view_data: dict, joined_bots: list, log_state: dict) -> dict:
    connections = current_region.get("connections") or []
    if not connections:
        return {
            "move_desire": 0.0,
            "best_region_id": None,
            "best_region_name": "None",
            "safe_directions": [],
            "all_evaluated_regions": []
        }
        
    our_hp = self_data.get("hp", 100)
    turn = view_data.get("turn") or 1
    
    active_death_zones = []
    if current_region.get("isDeathZone") or current_region.get("is_death_zone"):
        active_death_zones.append(current_region.get("id"))
        
    regions_list = view_data.get("visibleRegions") or view_data.get("regions") or []
    for r in regions_list:
        if isinstance(r, dict):
            if r.get("isDeathZone") or r.get("is_death_zone"):
                active_death_zones.append(r.get("id"))
                
    pending_dz_list = [pz.get("id") for pz in view_data.get("pendingDeathzones", []) if isinstance(pz, dict)]
    
    distances = calculate_distances(current_region, view_data)
    evaluated_routes = []
    
    for target_id in connections:
        target_name = target_id[:8]
        target_terrain = "plains"
        is_target_dz = target_id in active_death_zones
        has_bomb = False
        
        for r in regions_list:
            if isinstance(r, dict) and r.get("id") == target_id:
                target_name = r.get("name") or target_name
                target_terrain = r.get("terrain") or target_terrain
                
                r_items = r.get("items") or r.get("groundItems") or []
                for item in r_items:
                    item_name = ""
                    if isinstance(item, dict):
                        item_name = (item.get("displayName") or item.get("name") or "").lower()
                    elif isinstance(item, str):
                        item_name = item.lower()
                    if "bomb" in item_name:
                        has_bomb = True
                        break
                break
                
        terrain_key = target_terrain.lower().strip()
        terrain_stats = TERRAINS.get(terrain_key, TERRAINS["plains"])
        move_ep_extra = terrain_stats.get("move_ep_extra", 0)
        
        score = 50
        score -= (move_ep_extra * 25)
        
        if has_bomb:
            score -= 900
            
        if is_target_dz:
            score -= 1000
        if target_id in pending_dz_list:
            score -= 800
            
        recent_kills = log_state.get("recent_kill_zones") or []
        if target_id in recent_kills:
            score += 45
            
        hostile_regions = log_state.get("hostile_regions", {}) if log_state else {}
        if target_id in hostile_regions:
            try:
                current_turn_val = int(turn)
                damage_turn_val = int(hostile_regions[target_id])
                if current_turn_val - damage_turn_val <= 5:
                    score -= 300
            except Exception:
                pass
            
        visible_agents = view_data.get("visibleAgents") or []
        for agent in visible_agents:
            if isinstance(agent, dict):
                a_name = agent.get("name")
                if a_name == bot_name:
                    continue
                is_alive = agent.get("isAlive") or agent.get("is_alive", True)
                if is_alive:
                    enemy_r_id = agent.get("regionId") or agent.get("region_id")
                    if enemy_r_id == target_id:
                        enemy_hp = agent.get("hp", 100)
                        if enemy_hp < 40 and our_hp >= 50:
                            score += 35
                        elif enemy_hp >= 70 and our_hp < 40:
                            score -= 30
                            
        move_history = log_state.get("visited_regions") or []
        if move_history and move_history[-1] == target_id:
            score -= 20
            
        evaluated_routes.append({
            "region_id": target_id,
            "region_name": target_name,
            "score": score,
            "is_safe": score > -500
        })
        
    evaluated_routes.sort(key=lambda x: x["score"], reverse=True)
    
    best_route = evaluated_routes[0] if evaluated_routes else None
    
    move_desire = 0.0
    best_region_id = None
    best_region_name = "None"
    
    if best_route and best_route["is_safe"]:
        best_region_id = best_route["region_id"]
        best_region_name = best_route["region_name"]
        
    if current_region.get("id") in active_death_zones or current_region.get("id") in pending_dz_list:
        move_desire = 100.0
    else:
        move_desire = min(100.0, max(0.0, best_route["score"]))
        
    safe_directions = [r["region_id"] for r in evaluated_routes if r["is_safe"]]
    
    return {
        "move_desire": move_desire,
        "best_region_id": best_region_id,
        "best_region_name": best_region_name,
        "safe_directions": safe_directions,
        "all_evaluated_regions": evaluated_routes
    }