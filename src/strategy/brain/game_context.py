from typing import Dict, Any, List
from config import settings

class GameContext:
    
    def __init__(self):
        # Mengarahkan memori lokal ke database global aliansi agar otomatis tersinkronisasi
        self.map_graph = settings.SHARED_MAP_GRAPH
        self.region_names = settings.SHARED_REGION_NAMES
        
        self.visited_history: List[str] = []
        self.interacted_regions: List[str] = []
        self.opponents_data: Dict[str, List[Dict[str, Any]]] = {"players": [], "monsters": []}
        self.pending_deathzones: List[str] = []
        self.active_deathzones: List[str] = []
        self.last_action_type = "rest"
        self.history_actions: List[Dict[str, Any]] = []
        
        self.last_kills_count = 0
        self.last_attack_region = ""
        self.loot_targets: List[str] = []
        
        # Memori pengunci target pertempuran
        self.last_target_id = ""

    def update_map(self, current_region: Dict[str, Any], pending_zones: List[Dict[str, Any]]):
        region_id = current_region.get("id")
        region_name = current_region.get("name")
        
        if region_id and region_id not in self.map_graph:
            self.map_graph[region_id] = current_region.get("connections", [])
            
        if region_id and region_name:
            self.region_names[region_id] = region_name
            
        if region_id:
            if not self.visited_history or self.visited_history[-1] != region_id:
                self.visited_history.append(region_id)
                if len(self.visited_history) > 4:
                    self.visited_history.pop(0)

            # Record visited history globally for co-op routing
            if not settings.SHARED_VISITED_HISTORY or settings.SHARED_VISITED_HISTORY[-1] != region_id:
                settings.SHARED_VISITED_HISTORY.append(region_id)
                if len(settings.SHARED_VISITED_HISTORY) > 8:
                    settings.SHARED_VISITED_HISTORY.pop(0)
        
        self.pending_deathzones = []
        for zone in pending_zones:
            z_id = zone.get("id")
            z_name = zone.get("name")
            if z_id:
                self.pending_deathzones.append(z_id)
                if z_name:
                    self.region_names[z_id] = z_name
                # AMNESIA FIX: Permanently register pending zones to global deathzone memory
                if z_id not in settings.SHARED_ACTIVE_DEATHZONES:
                    settings.SHARED_ACTIVE_DEATHZONES.append(z_id)
        
        if current_region.get("isDeathZone"):
            if region_id not in self.active_deathzones:
                self.active_deathzones.append(region_id)
            # Register to global shared active deathzones
            if region_id not in settings.SHARED_ACTIVE_DEATHZONES:
                settings.SHARED_ACTIVE_DEATHZONES.append(region_id)