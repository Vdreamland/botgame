def get_vision_range(view: dict) -> float:
    if not view:
        return 1.0
    self_data = view.get("self", {})
    return float(self_data.get("vision", 1.0))

def get_layered_zones(view: dict) -> dict:
    result = {
        "layer_0": "Unknown",
        "layer_1": [],
        "visible_layers_count": 0,
        "total_visible_zones": 0
    }
    
    if not view or "currentRegion" not in view:
        return result

    current_region = view["currentRegion"]
    current_id = current_region.get("id") or current_region.get("name", "Unknown")
    result["layer_0"] = current_id
    
    connections = current_region.get("connections", [])
    layer_1 = [str(conn) for conn in connections if conn]
    result["layer_1"] = layer_1
    
    visible_count = 1
    layers_count = 0
    
    if layer_1:
        visible_count += len(layer_1)
        layers_count = 1
        
    result["visible_layers_count"] = layers_count
    result["total_visible_zones"] = visible_count
    
    return result