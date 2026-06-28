# -*- coding: utf-8 -*-
"""
ClawRoyale Inventory Cleaner and Pickup Manager.
Handles item collection, inventory limit checks, and drops obsolete items [11].
"""

from typing import Dict, Any, Optional, Tuple
from core.state.game_state import GameState
from config.item_registry import ITEM_DATABASE
from strategies.scanners.ground_item_scanner import GroundItemScanner


class InventoryManager:
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.scanner = GroundItemScanner(game_state)

    def determine_pickup_and_cleanup(self, max_slots: int = 10) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Determines the next inventory optimization step.
        ClawRoyale in-game inventory is strictly limited to 10 slots [skill.md].
        """
        best_ground_item = self.scanner.find_highest_utility_item()
        if not best_ground_item:
            return "NONE", None, None

        ground_item_id = best_ground_item.get("id") or best_ground_item.get("itemId") or ""
        ground_item_type = best_ground_item.get("type", "")

        inventory_items = getattr(self.game_state, "inventory", [])
        current_used_slots = len(inventory_items)

        if current_used_slots < max_slots:
            return "PICKUP", ground_item_id, ground_item_type

        item_to_drop_id = None
        lowest_value = 999.0

        for item in inventory_items:
            i_id = item.get("id", "")
            i_type = item.get("type", "")

            if i_type in ITEM_DATABASE:
                info = ITEM_DATABASE[i_type]
                category = info.get("category", "")
                
                val = 100.0
                if i_type == "Dagger" and self.game_state.equipped_weapon in ["Sword", "Katana"]:
                    val = 1.0
                elif i_type == "Bow" and self.game_state.equipped_weapon in ["Pistol", "Sniper rifle"]:
                    val = 1.0
                elif category == "consumable":
                    val = 20.0

                if val < lowest_value:
                    lowest_value = val
                    item_to_drop_id = i_id

        ground_item_utility = best_ground_item.get("utility_score", 0.0)
        if item_to_drop_id and ground_item_utility > 1.0:
            return "DROP_AND_PICKUP", ground_item_id, item_to_drop_id

        return "NONE", None, None