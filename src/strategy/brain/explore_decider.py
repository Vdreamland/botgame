from typing import Dict, Any, Optional
from src.strategy.brain.game_context import GameContext
from src.strategy.brain.base_decider import BaseDecider
from src.strategy.behaviors.utility_behavior import UtilityBehavior

class ExploreDecider(BaseDecider):
    
    def decide(self, view: Dict[str, Any], context: GameContext) -> Optional[Dict[str, Any]]:
        view_self = view.get("self", {})
        ep = view_self.get("ep", 10)
        alert_gauge = view_self.get("alertGauge", 0)
        alert_active = view_self.get("alertActive", False)
        
        current_region = view.get("currentRegion", {})
        current_region_id = current_region.get("id")
        
        visible_ruins = view.get("visibleRuins", [])
        
        current_ruin = None
        for ruin in visible_ruins:
            if ruin.get("ruinId") == current_region_id:
                current_ruin = ruin
                break
                
        if current_ruin and not current_ruin.get("isEmpty", True):
            if alert_active:
                context.last_action_type = "rest"
                return UtilityBehavior.build_rest_action(
                    thought=f"Alert is ACTIVE ({alert_gauge}/10). Resting to cool down and clear guardian targeting."
                )
                
            if ep >= 1:
                context.last_action_type = "explore"
                content_type = current_ruin.get("contentType", "relic")
                gauge_progress = current_ruin.get("gauge", 0)
                return UtilityBehavior.build_explore_action(
                    thought=f"Exploring {content_type} ruin. Progress: {gauge_progress}/3."
                )
                
        return None