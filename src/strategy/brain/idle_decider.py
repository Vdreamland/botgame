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