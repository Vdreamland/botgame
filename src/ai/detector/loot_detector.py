def parse_loot_status(agent_view_data):
    view = agent_view_data.get("view", {})
    current_region = view.get("currentRegion", {})
    current_region_id = current_region.get("id")
    
    visible_regions = view.get("visibleRegions", [])
    my_region_data = next((r for r in visible_regions if r.get("id") == current_region_id), {})
    
    ground_items = my_region_data.get("items", [])
    ground_item_names = [item.get("name", "Unknown Item") for item in ground_items]
    
    return {
        "ground_items": ground_item_names,
        "ground_item_count": len(ground_items)
    }