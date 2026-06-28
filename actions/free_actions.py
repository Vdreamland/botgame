# -*- coding: utf-8 -*-
"""
ClawRoyale Free Action Payloads.
Generates nested payloads for instant actions that consume 0 EP and bypass cooldown locks [13].
"""

from typing import Dict, Any


class FreeActionFactory:
    @staticmethod
    def create_equip_payload(item_id: str) -> Dict[str, Any]:
        """
        Creates payload to equip a weapon or armor from the inventory [9].
        """
        return {
            "type": "action",
            "data": {
                "type": "equip",
                "itemId": str(item_id)
            }
        }

    @staticmethod
    def create_pickup_payload(item_id: str) -> Dict[str, Any]:
        """
        Creates payload to pick up an item found on the current hex ground.
        """
        return {
            "type": "action",
            "data": {
                "type": "pickup",
                "itemId": str(item_id)
            }
        }

    @staticmethod
    def create_whisper_payload(target_id: str, message: str) -> Dict[str, Any]:
        """
        Sends a private text message to another player [13].
        """
        return {
            "type": "action",
            "data": {
                "type": "whisper",
                "targetId": str(target_id),
                "message": message[:200]
            }
        }

    @staticmethod
    def create_broadcast_payload(message: str) -> Dict[str, Any]:
        """
        Broadcasts a public text message to all players in the arena [13].
        """
        return {
            "type": "action",
            "data": {
                "type": "broadcast",
                "message": message[:200]
            }
        }