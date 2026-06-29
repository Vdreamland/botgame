import random
from typing import Dict, Any, Optional
from src.strategy.brain.game_context import GameContext
from src.strategy.brain.base_decider import BaseDecider
from src.strategy.behaviors.utility_behavior import UtilityBehavior
from src.strategy.navigation.pathfinder import Pathfinder
from config import settings

class IdleDecider(BaseDecider):
    
    def decide(self, view: Dict[str, Any], context: GameContext) -> Optional[Dict[str, Any]]:
        view_self = view.get("self", {})
        hp = view_self.get("hp", 100)
        ep = view_self.get("ep", 10)
        kills = view_self.get("kills", 0)
        current_turn = view.get("turn", 0)
        
        # 1. PLAYER KILLS RECORDING
        if kills > context.last_kills_count:
            context.last_kills_count = kills
            if context.last_attack_region and context.last_attack_region not in settings.SHARED_LOOT_TARGETS:
                settings.SHARED_LOOT_TARGETS.append(context.last_attack_region)
            
        # 2. MONSTER KILLS RECORDING
        if context.last_action_type == "attack" and context.last_attack_region:
            opponents_now = context.opponents_data.get("players", []) + context.opponents_data.get("monsters", [])
            opponents_still_in_target_region = any(
                opp.get("region_id") == context.last_attack_region for opp in opponents_now
            )
            if not opponents_still_in_target_region:
                if context.last_attack_region not in settings.SHARED_LOOT_TARGETS:
                    settings.SHARED_LOOT_TARGETS.append(context.last_attack_region)
                context.last_attack_region = ""

        current_region = view.get("currentRegion", {})
        current_region_id = current_region.get("id")
        connections = current_region.get("connections", [])
        
        if not connections:
            return None

        # Clean SOS signal if we arrived to support
        if settings.SOS_TARGETS and current_region_id == settings.SOS_TARGETS[0]:
            settings.SOS_TARGETS.pop(0)

        # Clean Shared Loot target if we arrived to loot
        if settings.SHARED_LOOT_TARGETS and current_region_id == settings.SHARED_LOOT_TARGETS[0]:
            settings.SHARED_LOOT_TARGETS.pop(0)

        # PRIORITY 1: RESPOND TO ALLY SOS CALLS (Helper must be healthy to avoid double casualties)
        if hp >= 60 and settings.SOS_TARGETS:
            target_region_id = settings.SOS_TARGETS[0]
            path = Pathfinder.find_shortest_path(current_region_id, target_region_id, context)
            if path and len(path) >= 2:
                next_step_id = path[1]
                context.last_action_type = "move"
                target_name = context.region_names.get(target_region_id, f"Hex-{target_region_id[:8]}")
                return UtilityBehavior.build_move_action(
                    region_id=next_step_id,
                    thought=f"Ally under threat! Navigating to backup site: {target_name}."
                )
            else:
                settings.SOS_TARGETS.pop(0)

        # PRIORITY 2: COOPERATIVE LOOT HARVESTING
        if settings.SHARED_LOOT_TARGETS:
            target_region_id = settings.SHARED_LOOT_TARGETS[0]
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
                settings.SHARED_LOOT_TARGETS.pop(0)
            
        safe_connections = [
            r_id for r_id in connections 
            if r_id not in context.pending_deathzones and r_id not in context.active_deathzones
        ]
        
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
            # Filter adjacent tiles using Shared Visited History for efficient split push
            unvisited = [r_id for r_id in chosen_connections if r_id not in settings.SHARED_VISITED_HISTORY]
            final_options = unvisited if unvisited else chosen_connections
            
            target_region_id = random.choice(final_options)
            context.last_action_type = "move"
            
            target_name = context.region_names.get(target_region_id, f"Hex-{target_region_id[:8]}")
            return UtilityBehavior.build_move_action(
                region_id=target_region_id, 
                thought=f"Exploring adjacent region: {target_name}"
            )
            
        return None