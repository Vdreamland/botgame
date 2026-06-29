from typing import Dict, Any, Tuple

class ThreatEvaluator:
    
    @staticmethod
    def scan_enemies(view: Dict[str, Any], self_id: str) -> Tuple[int, int]:
        current_region = view.get("currentRegion", {})
        current_region_id = current_region.get("id")
        
        visible_agents = view.get("visibleAgents", [])
        visible_monsters = view.get("visibleMonsters", [])
        
        inside_count = 0
        detected_count = 0

        for agent in visible_agents:
            if agent.get("id") == self_id:
                continue
            if agent.get("regionId") == current_region_id:
                inside_count += 1
            else:
                detected_count += 1

        for monster in visible_monsters:
            if monster.get("regionId") == current_region_id:
                inside_count += 1
            else:
                detected_count += 1

        return inside_count, detected_count