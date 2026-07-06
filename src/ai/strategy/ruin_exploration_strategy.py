class RuinExplorationStrategy:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        current_region = view.get("currentRegion", {})
        terrain = current_region.get("terrain", "").lower()
        
        if terrain == "ruins":
            return 68, {"action_type": "search"}
            
        return 22, {"action_type": "search"}