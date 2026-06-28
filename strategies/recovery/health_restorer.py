# -*- coding: utf-8 -*-
"""
ClawRoyale Health Restorer Strategy.
Analyzes current HP and selects the most optimal healing item from inventory.
"""

from typing import Dict, Any, Optional
from config.item_registry import ITEM_DATABASE
from core.state.game_state import GameState


class HealthRestorer:
    def __init__(self, game_state: GameState):
        self.game_state = game_state

    def determine_healing_action(self) -> Optional[Dict[str, Any]]:
        """
        Inspects the inventory and recommends using a specific healing item.
        Avoids over-healing waste (e.g. won't use Medkit if only 10 HP is missing).
        :return: Dict containing 'item_id' and 'heal_value' if use is recommended, else None.
        """
        current_hp = self.game_state.hp
        missing_hp = 100.0 - current_hp

        # Bot tidak membutuhkan penyembuhan jika kesehatannya di atas 95%
        if missing_hp <= 5.0:
            return None

        # Ambil daftar barang di tas (Asumsi game_state memiliki list inventory)
        inventory_items = getattr(self.game_state, "inventory", [])
        if not inventory_items:
            return None

        best_item: Optional[Dict[str, Any]] = None
        closest_fit_diff = 999.0

        for item in inventory_items:
            item_id = item.get("id", "")
            item_type = item.get("type", "")  # Kode tipe item dari item_registry

            if item_type in ITEM_DATABASE:
                info = ITEM_DATABASE[item_type]
                category = info.get("category", "")
                
                # Hanya evaluasi item dengan kategori consumable penyembuh
                if category == "consumable" and info.get("heal_value", 0) > 0:
                    heal_val = float(info.get("heal_value", 0))
                    
                    # Hitung perbedaan efisiensi penyembuhan
                    diff = abs(missing_hp - heal_val)
                    
                    # Prioritaskan item yang memiliki nilai penyembuhan paling pas dengan sisa HP
                    if diff < closest_fit_diff:
                        closest_fit_diff = diff
                        best_item = {
                            "item_id": item_id,
                            "item_type": item_type,
                            "heal_value": heal_val
                        }

        # Skenario Khusus: Jika HP bot di bawah 35% (Kritis), langsung paksa gunakan obat terbesar apa pun yang ada
        if current_hp < 35.0 and best_item is None:
            # Cari obat darurat apa pun
            for item in inventory_items:
                item_type = item.get("type", "")
                if item_type in ITEM_DATABASE:
                    info = ITEM_DATABASE[item_type]
                    if info.get("category") == "consumable" and info.get("heal_value", 0) > 0:
                        return {
                            "item_id": item.get("id"),
                            "item_type": item_type,
                            "heal_value": float(info.get("heal_value"))
                        }

        return best_item