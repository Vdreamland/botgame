import random
from typing import Dict, Any, Optional
from src.strategy.brain.game_context import GameContext
from src.strategy.brain.base_decider import BaseDecider
from src.strategy.behaviors.utility_behavior import UtilityBehavior
from src.strategy.navigation.pathfinder import Pathfinder

class IdleDecider(BaseDecider):
    
    def decide(self, view: Dict[str, Any], context: GameContext) -> Optional[Dict[str, Any]]:
        view_self = view.get("self", {})
        ep = view_self.get("ep", 10)
        kills = view_self.get("kills", 0)
        current_turn = view.get("turn", 0)
        
        # 1. Perekaman target pemanenan jasad jika angka Kills bertambah
        if kills > context.last_kills_count:
            context.last_kills_count = kills
            if context.last_attack_region and context.last_attack_region not in context.loot_targets:
                context.loot_targets.append(context.last_attack_region)
            
        current_region = view.get("currentRegion", {})
        current_region_id = current_region.get("id")
        connections = current_region.get("connections", [])
        
        if not connections:
            return None

        # 2. Pembersihan Target: Jika sudah sampai di wilayah jasad musuh, hapus dari target antrean
        if context.loot_targets and current_region_id == context.loot_targets[0]:
            context.loot_targets.pop(0)

        # 3. Menuntun bot melangkah menggunakan Pathfinder jika ada target jasad terdaftar
        if context.loot_targets:
            target_region_id = context.loot_targets[0]
            path = Pathfinder.find_shortest_path(current_region_id, target_region_id, context)
            if path and len(path) >= 2:
                next_step_id = path[1]
                context.last_action_type = "move"
                target_name = context.region_names.get(target_region_id, f"Hex-{target_region_id[:8]}")
                return UtilityBehavior.build_move_action(
                    region_id=next_step_id,
                    thought=f"Matchmaking loot target confirmed. Navigating to secured kill site: {target_name}."
                )
            else:
                context.loot_targets.pop(0)
            
        safe_connections = [
            r_id for r_id in connections 
            if r_id not in context.pending_deathzones and r_id not in context.active_deathzones
        ]
        
        # 4. Filter Tambahan: Menghindari area pojokan (koneksi <= 3) secara proaktif saat kondisi aman
        # Di fase akhir (Turn > 15), filter pojokan ini diwajibkan secara mutlak
        if current_turn > 15 and safe_connections:
            safe_non_corners = [
                r_id for r_id in safe_connections
                if len(context.map_graph.get(r_id, [1, 2, 3, 4])) > 3
            ]
            if safe_non_corners:
                safe_connections = safe_non_corners
        else:
            safe_non_corners = [
                r_id for r_id in safe_connections
                if len(context.map_graph.get(r_id, [1, 2, 3, 4])) > 3
            ]
        
        pending_connections = [
            r_id for r_id in connections 
            if r_id not in context.active_deathzones
        ]
        
        if safe_non_corners and current_turn <= 15:
            chosen_connections = safe_non_corners
        else:
            chosen_connections = safe_connections if safe_connections else (pending_connections if pending_connections else connections)
        
        if chosen_connections:
            # 5. Filter Riwayat Kunjungan (Anti Ping-pong)
            unvisited = [r_id for r_id in chosen_connections if r_id not in context.visited_history]
            final_options = unvisited if unvisited else chosen_connections
            
            target_region_id = random.choice(final_options)
            context.last_action_type = "move"
            
            target_name = context.region_names.get(target_region_id, f"Hex-{target_region_id[:8]}")
            return UtilityBehavior.build_move_action(
                region_id=target_region_id, 
                thought=f"Exploring adjacent region: {target_name}"
            )
            
        return None