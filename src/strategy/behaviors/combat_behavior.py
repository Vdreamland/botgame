from typing import Dict, Any

class CombatBehavior:
    
    @staticmethod
    def build_attack_action(target_id: str, thought: str = "") -> Dict[str, Any]:
        payload = {
            "type": "action",
            "data": {
                "type": "attack",
                "targetId": target_id
            }
        }
        if thought:
            payload["thought"] = thought[:700]
        return payload