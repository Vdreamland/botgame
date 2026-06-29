import random
from typing import Dict, Any, Optional
from src.strategy.brain.game_context import GameContext
from src.strategy.brain.base_decider import BaseDecider
from src.strategy.behaviors.utility_behavior import UtilityBehavior

class SurvivalDecider(BaseDecider):
    
    def decide(self, view: Dict[str, Any], context: GameContext) -> Optional[Dict[str, Any]]:
        view_self = view.get("self", {})
        hp = view_self.get("hp", 100)
        ep = view_self.get("ep", 10)
        inventory = view_self.get("inventory", [])
        current_region = view.get("currentRegion", {})
        region_id = current_region.get("id")

        if hp < 50:
            for item in inventory:
                if isinstance(item, dict):
                    item_name = item.get("name") or item.get("displayName") or ""
                    item_id = item.get("id", "")
                    if item_name in ["Medkit", "Emergency Food", "Bandage"] and item_id:
                        context.last_action_type = "use_item"
                        return UtilityBehavior.build_use_item_action(
                            item_id=item_id,
                            thought=f"HP critical ({hp}/100). Consuming {item_name} to heal."
                        )

        if ep < 2:
            for item in inventory:
                if isinstance(item, dict):
                    item_name = item.get("name") or item.get("displayName") or ""
                    item_id = item.get("id", "")
                    if item_name in ["Energy Drink", "Medkit"] and item_id:
                        context.last_action_type = "use_item"
                        return UtilityBehavior.build_use_item_action(
                            item_id=item_id,
                            thought=f"Energy critical ({ep}/10). Consuming {item_name} to recover EP."
                        )

        if hp < 70:
            interactables = current_region.get("interactables", [])
            for fac in interactables:
                if isinstance(fac, dict):
                    fac_name = fac.get("name", "")
                    is_used = fac.get("isUsed", True)
                    if fac_name == "Medical Facility" and not is_used:
                        context.last_action_type = "interact"
                        return UtilityBehavior.build_interact_action(
                            thought="HP low. Interacting with Medical Facility to heal."
                        )

        in_danger_zone = (region_id in context.pending_deathzones or region_id in context.active_deathzones)
        visible_agents = view.get("visibleAgents", [])
        enemies_here = [a for a in visible_agents if a.get("id") != view_self.get("id") and a.get("regionId") == region_id]
        
        if in_danger_zone or (hp < 40 and enemies_here):
            connections = current_region.get("connections", [])
            safe_options = [
                r_id for r_id in connections 
                if r_id not in context.pending_deathzones and r_id not in context.active_deathzones
            ]
            
            if safe_options:
                target_id = random.choice(safe_options)
                context.last_action_type = "move"
                target_name = context.region_names.get(target_id, f"Hex-{target_id[:8]}")
                return UtilityBehavior.build_move_action(
                    region_id=target_id,
                    thought=f"HP low or Zone shrinking. Escaping to adjacent safe region: {target_name}"
                )

        return None