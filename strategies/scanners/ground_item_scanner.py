# -*- coding: utf-8 -*-
"""
ClawRoyale Ground Item Scanner.
Finds and ranks items on the ground based on the agent's real-time tactical needs [9].
"""

from typing import Dict, Any, List, Optional
from core.state.game_state import GameState
from config.item_registry import ITEM_DATABASE


class GroundItemScanner:
    def __init__(self, game_state: GameState):
        self.game_state = game_state

    def find_highest_utility_item(self) -> Optional[Dict[str, Any]]:
        """
        Scans ground items and scores them.
        Returns the item coordinate with the highest utility score.
        """
        items = self.game_state.items_on_ground
        if not items:
            return None

        best_item: Optional[Dict[str, Any]] = None
        highest_score = -1.0

        for item in items:
            # Pengaman berlapis mencari ID item asli dari server
            item_id = item.get("id") or item.get("itemId") or ""
            
            # Pengaman berlapis membaca tipe barang asli dari payload WebSocket game
            item_type = item.get("type") or item.get("name") or item.get("itemType") or item.get("item_type") or ""
            
            # Semua item di lobi lurus berada di lantai wilayah yang sama berjarak 0
            distance = 0

            # Hitung skor utilitas item tersebut
            score = self._calculate_item_utility(item_type, distance)
            
            if score > highest_score:
                highest_score = score
                best_item = item.copy()
                best_item["id"] = item_id
                best_item["itemId"] = item_id
                best_item["type"] = item_type
                best_item["distance"] = distance
                best_item["utility_score"] = score

        # Hanya kembalikan jika utilitasnya bernilai positif
        if highest_score > 0.0:
            return best_item
        return None

    def _calculate_item_utility(self, item_type: str, distance: int) -> float:
        """
        Internal utility scorer.
        Evaluates dynamic needs (e.g., low HP needs healing items, incomplete sets need relics) [9].
        Safe against any server case-sensitivity or underscores.
        """
        if not item_type:
            return 0.0

        # Normalisasi pencarian tipe item agar aman terhadap case-sensitivity dan format snake_case
        normalized_search = item_type.lower().replace("_", " ").strip()
        matched_info = None
        
        for db_key, db_info in ITEM_DATABASE.items():
            if db_key.lower().replace("_", " ").strip() == normalized_search:
                matched_info = db_info
                break

        if not matched_info:
            return 0.0

        category = matched_info.get("category", "")
        
        # Penalti jarak (Item yang jauh dinilai kurang bernilai karena memakan EP gerakan)
        distance_penalty = distance * 0.15
        base_utility = 1.0

        # Kasus 1: Bot sekarat (HP < 40%) -> Utilitas obat sangat tinggi
        if category == "consumable" and matched_info.get("heal_value", 0) > 0:
            hp_percentage = self.game_state.hp / 100.0
            if hp_percentage < 0.40:
                base_utility = 2.5
            elif hp_percentage >= 0.85:
                # Sedikit berguna jika darah penuh, namun tetap diprioritaskan jika tas muat
                base_utility = 0.2

        # Kasus 2: Relic pengisi fullSet (Bot butuh melengkapi RGB Relic) [9]
        elif category == "relic":
            slot_color = matched_info.get("slot_color", "")
            # Jika bot belum punya relic di warna ini, jadikan prioritas tinggi untuk fullSet [9]
            if slot_color not in self.game_state.equipped_relics:
                base_utility = 2.0
            else:
                base_utility = 0.3

        # Kasus 3: Senjata (Weapon)
        elif category == "weapon":
            # Jika bot belum memegang senjata, senjata apa pun sangat berharga
            if not self.game_state.equipped_weapon:
                base_utility = 1.8
            else:
                base_utility = 0.5

        final_score = base_utility - distance_penalty
        return max(0.0, final_score)