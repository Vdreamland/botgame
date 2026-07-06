from src.ai.strategy.priority.equipped_priority import EquippedPriority
from src.ai.strategy.priority.ground_loot_priority import GroundLootPriority
from src.ai.strategy.priority.interact_priority import InteractPriority
from src.ai.strategy.priority.recovery_priority import RecoveryPriority
from src.ai.strategy.priority.target_kill_priority import TargetKillPriority
from src.ai.strategy.navigation_strategy import NavigationStrategy
from src.ai.strategy.ruin_exploration_strategy import RuinExplorationStrategy

from src.utils.action_helper import (
    create_move_action,
    create_attack_action,
    create_loot_action,
    create_search_action,
    create_use_item_action,
    create_equip_action,
    create_rest_action
)

class DecisionMaker:
    def __init__(self):
        self.priorities = [
            EquippedPriority(),
            GroundLootPriority(),
            InteractPriority(),
            RecoveryPriority(),
            TargetKillPriority(),
            NavigationStrategy(),
            RuinExplorationStrategy()
        ]

    def make_decision(self, manager, raw_data):
        best_score = -1
        best_action = None
        
        for priority in self.priorities:
            score, action = priority.evaluate(manager, raw_data)
            if score > best_score and action:
                best_score = score
                best_action = action
                
        if not best_action:
            return create_search_action()
            
        action_type = best_action.get("action_type")
        
        if action_type == "equip":
            return create_equip_action(best_action["item_id"])
        elif action_type == "loot":
            return create_loot_action(best_action["item_id"])
        elif action_type == "use_item":
            return create_use_item_action(best_action["item_id"])
        elif action_type == "attack":
            return create_attack_action(best_action["target_id"])
        elif action_type == "move":
            return create_move_action(best_action["destination"])
        elif action_type == "rest":
            return create_rest_action()
        elif action_type == "search":
            return create_search_action()
        elif action_type == "interact":
            return {
                "type": "action",
                "data": {
                    "actionType": "interact",
                    "params": {
                        "facility": best_action["facility_id"]
                    }
                }
            }
            
        return create_search_action()