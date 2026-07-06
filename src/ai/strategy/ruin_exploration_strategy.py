class RuinExplorationStrategy:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        current_region = view.get("currentRegion", {})
        current_region_id = current_region.get("id")
        
        if not current_region_id:
            return 0, None
            
        ruin_data = current_region.get("ruin")
        is_ruin = current_region.get("isRuin", False) or ruin_data is not None
        
        if is_ruin:
            if ruin_data and ruin_data.get("isEmpty", False):
                return 0, None
                
            searched_regions = getattr(manager, "searched_regions", set())
            if current_region_id in searched_regions:
                return 0, None
                
            return 68, {"action_type": "explore"}
            
        return 0, None