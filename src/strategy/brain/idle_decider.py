import random
from typing import Dict, Any, Optional
from src.strategy.brain.game_context import GameContext
from src.strategy.brain.base_decider import BaseDecider
from src.strategy.behaviors.utility_behavior import UtilityBehavior

class IdleDecider(BaseDecider):
    
    def decide(self, view: Dict[str, Any], context: GameContext) -> Optional[Dict[str, Any]]:
        view_self = view.get("self", {})
        ep = view_self.get("ep", 10)
        
        if ep < 4:
            context.last_action_type = "rest"
            return UtilityBehavior.build_rest_action(thought="Energy low. Rest to recover EP.")
            
        current_region = view.get("currentRegion", {})
        connections = current_region.get("connections", [])
        
        if not connections:
            return None
            
        safe_connections = [
            r_id for r_id in connections 
            if r_id not in context.pending_deathzones and r_id not in context.active_deathzones
        ]
        
        pending_connections = [
            r_id for r_id in connections 
            if r_id not in context.active_deathzones
        ]
        
        chosen_connections = safe_connections if safe_connections else (pending_connections if pending_connections else connections)
        
        if chosen_connections:
            # ALGORITMA PENGHINDARAN POJOKAN MAP (Corner & Edge Avoidance Heuristics)
            # Menilai kelayakan wilayah tetangga berdasarkan jumlah koneksi yang terekam di ingatan bot
            def calculate_region_safety_score(r_id: str) -> int:
                if r_id in context.map_graph:
                    neighbors_count = len(context.map_graph[r_id])
                    # Jika koneksi <= 3, ini adalah pojokan/tepi map yang sangat rawan terjebak. Beri skor penalti terendah!
                    if neighbors_count <= 3:
                        return 1
                    return neighbors_count
                # Nilai default jika wilayah tersebut belum pernah dikunjungi/direkam koneksinya
                return 4

            # Menyortir pilihan jalan agar bot selalu melangkah ke wilayah yang paling kaya koneksi (menuju pusat peta)
            chosen_connections.sort(key=calculate_region_safety_score, reverse=True)
            target_region_id = chosen_connections[0]
            
            context.last_action_type = "move"
            target_name = context.region_names.get(target_region_id, f"Hex-{target_region_id[:8]}")
            return UtilityBehavior.build_move_action(
                region_id=target_region_id, 
                thought=f"Exploring safe, well-connected region: {target_name}"
            )
            
        return None