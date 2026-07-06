from src.game_data import MONSTERS, GUARDIANS

class TargetKillPriority:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        self_data = view.get("self", {})
        my_id = self_data.get("id")
        current_region_id = view.get("currentRegion", {}).get("id")
        
        if not current_region_id:
            return 0, None
            
        visible_agents = view.get("visibleAgents", [])
        visible_monsters = view.get("visibleMonsters", [])
        
        for agent in visible_agents:
            agent_id = agent.get("id")
            region_id = agent.get("regionId")
            if agent_id and agent_id != my_id and region_id == current_region_id:
                if agent.get("isAlive", True):
                    return 93, {"action_type": "attack", "target_id": agent_id}
                    
        for monster in visible_monsters:
            monster_id = monster.get("id")
            region_id = monster.get("regionId")
            if dist := manager.current_distances.get(region_id):
                if dist > 0:
                    continue
            monster_name = monster.get("name", "")
            if monster_id and region_id == current_region_id:
                if monster.get("isAlive", True):
                    if monster_name in GUARDIANS:
                        return 85, {"action_type": "attack", "target_id": monster_id}
                    return 77, {"action_type": "attack", "target_id": monster_id}
                    
        return 0, None