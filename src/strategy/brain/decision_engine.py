from typing import Dict, Any, Optional, List
from src.strategy.brain.game_context import GameContext
from src.strategy.brain.base_decider import BaseDecider
from src.strategy.brain.survival_decider import SurvivalDecider
from src.strategy.brain.combat_decider import CombatDecider
from src.strategy.brain.utility_decider import UtilityDecider
from src.strategy.brain.idle_decider import IdleDecider

class DecisionEngine:
    
    def __init__(self):
        self.deciders: List[BaseDecider] = [
            SurvivalDecider(),
            CombatDecider(),
            UtilityDecider(),
            IdleDecider()
        ]

    def compute_action(self, view: Dict[str, Any], context: GameContext) -> Optional[Dict[str, Any]]:
        for decider in self.deciders:
            action = decider.decide(view, context)
            if action:
                return action
        return None