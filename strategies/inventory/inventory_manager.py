# -*- coding: utf-8 -*-
"""
ClawRoyale Inventory Cleaner and Pickup Manager.
Handles item collection, inventory limit checks, and drops obsolete items [15].
"""

from typing import Dict, Any, Optional, Tuple
from core.state.game_state import GameState
from config.item_registry import ITEM_DATABASE
from strategies.scanners.ground_item_scanner import GroundItemScanner


class InventoryManager:
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.scanner = GroundItemScanner(game_state)

    def determine_pickup_and_cleanup(self, max_slots: int = 15) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Determines the next inventory optimization step.
        :param max_slots: Current inventory slot limit of the agent.
        :return: Tuple of (action_type, target_item_id, details)
        
        Actions:
        - "PICKUP": Safe to pick up target item on ground.
        - "DROP_AND_PICKUP": Drop an obsolete item first to free space, then pick up new item.
        - "NONE": No inventory actions recommended.
        """
        # 1. Cari item dengan utilitas tertinggi di tanah sekitar [9]
        best_ground_item = self.scanner.find_highest_utility_item()
        if not best_ground_item:
            return "NONE", None, None

        ground_item_id = best_ground_item.get("itemId", "")
        ground_item_type = best_ground_item.get("type", "")

        # Ambil jumlah barang bawaan saat ini di dalam tas
        inventory_items = getattr(self.game_state, "inventory", [])
        current_used_slots = len(inventory_items)

        # Skenario A: Tas masih muat -> Langsung ambil item [13]
        if current_used_slots < max_slots:
            return "PICKUP", ground_item_id, ground_item_type

        # Skenario B: Tas penuh -> Cari apakah ada item sampah di tas yang bernilai lebih rendah
        item_to_drop_id: Optional[str] = None
        lowest_value = 999.0

        # Cari item dengan nilai terendah di tas untuk dibuang
        for item in inventory_items:
            i_id = item.get("id", "")
            i_type = item.get("type", "")

            if i_type in ITEM_DATABASE:
                info = ITEM_DATABASE[i_type]
                category = info.get("category", "")
                
                # Prioritaskan membuang senjata berkarat (Rusty) jika kita sudah memegang senjata steel [11]
                val = 100.0
                if i_type == "weap_rust_blade" and self.game_state.equipped_weapon == "weap_steel_sword":
                    val = 1.0  # Sangat tidak bernilai
                elif category == "consumable":
                    val = 20.0 # Boleh dibuang jika kita butuh slot relic/weapon baru

                if val < lowest_value:
                    lowest_value = val
                    item_to_drop_id = i_id

        # Hanya lakukan buang-ambil jika item baru di tanah memiliki utilitas lebih tinggi dibanding barang terburuk di tas
        ground_item_utility = best_ground_item.get("utility_score", 0.0)
        if item_to_drop_id and ground_item_utility > 1.0:
            return "DROP_AND_PICKUP", ground_item_id, item_to_drop_id

        return "NONE", None, None