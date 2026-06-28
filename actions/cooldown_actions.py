# -*- coding: utf-8 -*-
"""
ClawRoyale Cooldown Action Payloads.
Generates compliant payloads for actions that consume EP and trigger 30s cooldowns [12].
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
            "action": "move",
            "q": q,
            "r": r
        }

    @staticmethod
    def create_explore_payload() -> Dict[str, Any]:
        """
        Creates payload to explore ruins at the agent's current position [10].
        """
        return {
            "type": "action",
            "action": "explore"
        }

    @staticmethod
    def create_attack_payload(target_id: str) -> Dict[str, Any]:
        """
        Creates payload to attack a hostile player or guardian at adjacent range [11].
        """
        return {
            "type": "action",
            "action": "attack",
            "targetId": target_id
        }

    @staticmethod
    def create_rest_payload() -> Dict[str, Any]:
        """
        Creates payload to rest and replenish Energy Points (EP).
        """
        return {
            "type": "action",
            "action": "rest"
        }

    @staticmethod
    def create_interact_payload() -> Dict[str, Any]:
        """
        Creates payload to interact with environmental objects on the tile.
        """
        return {
            "type": "action",
            "action": "interact"
        }