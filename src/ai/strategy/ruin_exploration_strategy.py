class RuinExplorationStrategy:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        self_data = view.get("self", {})
        my_id = self_data.get("id")
        hp = self_data.get("hp", 100)
        
        current_region = view.get("currentRegion", {})
        current_region_id = current_region.get("id")
        
        is_ruin = "ruinGauge" in current_region or current_region.get("name", "").startswith("S:")
        
        if is_ruin:
            is_empty = current_region.get("isEmpty", False)
            if is_empty:
                return 0, None
            
            has_alive_monsters_here = False
            for monster in view.get("visibleMonsters", []):
                if monster.get("regionId") == current_region_id and monster.get("isAlive", True):
                    has_alive_monsters_here = True
                    break
            
            has_alive_enemies_here = False
            for agent in view.get("visibleAgents", []):
                if agent.get("id") != my_id and agent.get("regionId") == current_region_id and agent.get("isAlive", True):
                    has_alive_enemies_here = True
                    break
            
            if has_alive_monsters_here or has_alive_enemies_here:
                return 0, None
                
            return 68, {"action_type": "explore"}
            
        return 0, None