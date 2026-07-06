def parse_deadzone_status(agent_view_data, distances):
    view = agent_view_data.get("view", {})
    current_region = view.get("currentRegion", {})
    current_region_id = current_region.get("id")
    
    pending_regions = view.get("pendingDeathzones", [])
    pending_ids = {r.get("id") for r in pending_regions if r.get("id")}
    
    current_status = "Safe"
    if current_region.get("isDeathZone"):
        current_status = "Deadzone"
    elif current_region_id in pending_ids:
        current_status = "Pending"
        
    visible_regions = view.get("visibleRegions", [])
    region_map = {r.get("id"): r for r in visible_regions if r.get("id")}
    if current_region_id not in region_map:
        region_map[current_region_id] = current_region
        
    active_deadzones = []
    pending_deadzones = []
    
    for r_id, dist in distances.items():
        if dist == 0:
            continue
            
        r_data = region_map.get(r_id, {})
        r_name = r_data.get("name", "Unknown")
        
        is_dead = r_data.get("isDeathZone", False)
        is_pending = r_id in pending_ids
        
        if is_dead:
            active_deadzones.append({"name": r_name, "layer": dist})
        elif is_pending:
            pending_deadzones.append({"name": r_name, "layer": dist})
            
    active_deadzones.sort(key=lambda x: x["layer"])
    pending_deadzones.sort(key=lambda x: x["layer"])
    
    return {
        "current_region_status": current_status,
        "active_deadzones": active_deadzones,
        "pending_deadzones": pending_deadzones
    }