# -*- coding: utf-8 -*-
"""
ClawRoyale Free Action Payloads.
Generates payloads for instant actions that consume 0 EP and bypass cooldown locks [13].
"""

from typing import Dict, Any


class FreeActionFactory:
    @staticmethod
    def create_equip_payload(item_id: str, slot: str) -> Dict[str, Any]:
        """
        Creates payload to equip a weapon or armor from the inventory [9].
        :param item_id: Unique database ID of the item in inventory.
        :param slot: Target slot ('weapon' or 'armor').
        """
        return {
            "type": "action",
            "action": "equip",
            "itemId": item_id,
            "slot": slot
        }

    @staticmethod
    def create_pickup_payload(item_id: str) -> Dict[str, Any]:
        """
        Creates payload to pick up an item found on the current hex ground.
        """
        return {
            "type": "action",
            "action": "pickup",
            "itemId": item_id
        }

    @staticmethod
    def create_whisper_payload(target_id: str, message: str) -> Dict[str, Any]:
        """
        Sends a private text message to another player (ideal for teammate bot synchronization) [13].
        """
        return {
            "type": "action",
            "action": "whisper",
            "targetId": target_id,
            "message": message
        }

    @staticmethod
    def create_broadcast_payload(message: str) -> Dict[str, Any]:
        """
        Broadcasts a public text message to all players in the arena [13].
        """
        return {
            "type": "action",
            "action": "broadcast",
            "message": message
        }