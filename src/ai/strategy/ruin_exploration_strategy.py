class RuinExplorationStrategy:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        current_region = view.get("currentRegion", {})
        
        is_ruin = "ruinGauge" in current_region or current_region.get("name", "").startswith("S:")
        
        if is_ruin:
            is_empty = current_region.get("isEmpty", False)
            if is_empty:
                return 0, None
            
            if getattr(manager, "has_layer_0_enemies", False):
                return 0, None
                
            return 68, {"action_type": "explore"}
            
        return 0, None