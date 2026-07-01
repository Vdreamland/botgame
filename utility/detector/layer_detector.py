# utility/detector/layer_detector.py

def detect_layers(bot_name: str, self_data: dict, current_region: dict, view_data: dict, joined_bots: list) -> list:
    curr_id = current_region.get("id")
    
    graph = {}
    regions = view_data.get("visibleRegions") or view_data.get("regions") or []
    all_regions = list(regions)
    
    found_curr = False
    for r in all_regions:
        if isinstance(r, dict) and r.get("id") == curr_id:
            found_curr = True
            break
    if not found_curr and current_region:
        all_regions.append(current_region)

    for r in all_regions:
        if isinstance(r, dict):
            r_id = r.get("id")
            connections = r.get("connections", [])
            if r_id:
                graph[r_id] = connections

    distances = {}
    if curr_id:
        distances[curr_id] = 0
        queue = [curr_id]
        head = 0
        while head < len(queue):
            node = queue[head]
            head += 1
            curr_dist = distances[node]
            for neighbor in graph.get(node, []):
                if neighbor not in distances:
                    distances[neighbor] = curr_dist + 1
                    queue.append(neighbor)

    layer_counts = {}
    for r_id, dist in distances.items():
        if dist not in layer_counts:
            layer_counts[dist] = {"P": 0, "M": 0, "A": 0}

    if 0 not in layer_counts:
        layer_counts[0] = {"P": 0, "M": 0, "A": 0}

    visible_agents = view_data.get("visibleAgents") or []
    for agent in visible_agents:
        if isinstance(agent, dict):
            a_name = agent.get("name", "")
            
            if a_name == bot_name:
                continue
                
            r_id = (
                agent.get("regionId") or 
                agent.get("region_id") or 
                agent.get("currentRegionId") or 
                agent.get("currentRegion", {}).get("id")
            )
            
            layer = distances.get(r_id)
            if layer is not None:
                if layer not in layer_counts:
                    layer_counts[layer] = {"P": 0, "M": 0, "A": 0}
                
                if a_name in joined_bots:
                    layer_counts[layer]["A"] += 1
                else:
                    layer_counts[layer]["P"] += 1

    visible_monsters = view_data.get("visibleMonsters") or []
    for monster in visible_monsters:
        if isinstance(monster, dict):
            r_id = (
                monster.get("regionId") or 
                monster.get("region_id") or 
                monster.get("currentRegionId") or 
                monster.get("currentRegion", {}).get("id")
            )
            
            layer = distances.get(r_id)
            if layer is not None:
                if layer not in layer_counts:
                    layer_counts[layer] = {"P": 0, "M": 0, "A": 0}
                layer_counts[layer]["M"] += 1

    max_layer = max(layer_counts.keys()) if layer_counts else 0
    sorted_layers = []
    for l in range(max_layer + 1):
        counts = layer_counts.get(l, {"P": 0, "M": 0, "A": 0})
        sorted_layers.append({
            "layer": l,
            "P": counts["P"],
            "M": counts["M"],
            "A": counts["A"]
        })

    return sorted_layers