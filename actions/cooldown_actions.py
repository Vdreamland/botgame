# -*- coding: utf-8 -*-
"""
ClawRoyale Cooldown Action Payloads.
Generates compliant nested payloads for actions that consume EP and trigger 30s cooldowns [12].
"""

from typing import Dict, Any


class CooldownActionFactory:
    @staticmethod
    def create_move_payload(q: int, r: int) -> Dict[str, Any]:
        """
        Creates payload to move the agent to specific hex coordinates (q, r) [8].
        """
        return {
            "type": "action",
            "data": {
                "type": "move",
                "q": int(q),
                "r": int(r)
            }
        }

    @staticmethod
    def create_explore_payload() -> Dict[str, Any]:
        """
        Creates payload to explore ruins at the agent's current position [10].
        """
        return {
            "type": "action",
            "data": {
                "type": "explore"
            }
        }

    @staticmethod
    def create_attack_payload(target_id: str) -> Dict[str, Any]:
        """
        Creates payload to attack a hostile player or guardian at adjacent range [11].
        """
        return {
            "type": "action",
            "data": {
                "type": "attack",
                "targetId": str(target_id)
            }
        }

    @staticmethod
    def create_rest_payload() -> Dict[str, Any]:
        """
        Creates payload to rest and replenish Energy Points (EP).
        """
        return {
            "type": "action",
            "data": {
                "type": "rest"
            }
        }

    @staticmethod
    def create_interact_payload() -> Dict[str, Any]:
        """
        Creates payload to interact with environmental objects on the tile.
        """
        return {
            "type": "action",
            "data": {
                "type": "interact"
            }
        }