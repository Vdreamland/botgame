from typing import Dict, Any, Optional
from src.strategy.brain.game_context import GameContext

class BaseDecider:
    
    def __init__(self):
        pass
        
    def decide(self, view: Dict[str, Any], context: GameContext) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("Each decider must implement the decide method.")