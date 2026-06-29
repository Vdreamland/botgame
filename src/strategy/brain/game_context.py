from typing import Dict, Any, List

class GameContext:
    
    def __init__(self):
        self.map_graph: Dict[str, List[str]] = {}
        self.region_names: Dict[str, str] = {}  # Kamus perekam nama wilayah
        self.pending_deathzones: List[str] = []
        self.active_deathzones: List[str] = []
        self.last_action_type: str = "rest"
        self.history_actions: List[Dict[str, Any]] = []

    def update_map(self, current_region: Dict[str, Any], pending_zones: List[Dict[str, Any]]):
        region_id = current_region.get("id")
        region_name = current_region.get("name")
        
        if region_id and region_id not in self.map_graph:
            self.map_graph[region_id] = current_region.get("connections", [])
            
        if region_id and region_name:
            self.region_names[region_id] = region_name
        
        self.pending_deathzones = []
        for zone in pending_zones:
            z_id = zone.get("id")
            z_name = zone.get("name")
            if z_id:
                self.pending_deathzones.append(z_id)
                if z_name:
                    self.region_names[z_id] = z_name
        
        if current_region.get("isDeathZone") and region_id not in self.active_deathzones:
            self.active_deathzones.append(region_id)