class RuinExplorationStrategy:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        current_region = view.get("currentRegion", {})
        current_region_id = current_region.get("id")
        terrain = current_region.get("terrain", "").lower()
        
        if terrain == "ruins" and current_region_id:
            visible_ruins = view.get("visibleRuins", [])
            ruin_data = next((r for r in visible_ruins if r.get("ruinId") == current_region_id), None)
            
            if ruin_data and ruin_data.get("isEmpty", False):
                return 0, None
                
            return 68, {"action_type": "search"}
            
        return 0, None