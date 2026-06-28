# -*- coding: utf-8 -*-
"""
ClawRoyale Auto Equipment Selector.
Optimizes weapon choices and completes Red/Green/Blue relic sets to trigger 'fullSet' [9].
"""

from typing import Dict, Any, Optional, Tuple, List, Set
from config.item_registry import ITEM_DATABASE
from core.state.game_state import GameState


class EquipSelector:
    def __init__(self, game_state: GameState):
        self.game_state = game_state

    def determine_optimal_equips(self) -> Optional[Tuple[str, str]]:
        """
        Scans inventory and identifies if equipping an item improves combat stats
        or completes the 'fullSet' requirement [9].
        :return: Tuple (item_id, slot_name) if equip is recommended, else None.
        """
        inventory_items = getattr(self.game_state, "inventory", [])
        if not inventory_items:
            return None

        # 1. OPTIMALISASI SENJATA (WEAPONS)
        best_weapon_id: Optional[str] = None
        highest_weapon_atk = 0.0

        # Ambil status serangan senjata terpasang saat ini [11]
        current_weapon_type = self.game_state.equipped_weapon
        if current_weapon_type in ITEM_DATABASE:
            highest_weapon_atk = float(ITEM_DATABASE[current_weapon_type].get("atk_bonus", 0.0))

        for item in inventory_items:
            item_id = item.get("id", "")
            item_type = item.get("type", "")

            if item_type in ITEM_DATABASE:
                info = ITEM_DATABASE[item_type]
                if info.get("category") == "weapon":
                    atk_bonus = float(info.get("atk_bonus", 0.0))
                    # Jika menemukan senjata dengan serangan lebih tinggi, jadikan target pasang [11]
                    if atk_bonus > highest_weapon_atk:
                        highest_weapon_atk = atk_bonus
                        best_weapon_id = item_id

        if best_weapon_id:
            return best_weapon_id, "weapon"

        # 2. OPTIMALISASI RELIC (MENGEJAR BONUS fullSet RGB) [9]
        equipped_relic_types = self.game_state.equipped_relics  # List tipe relic yang terpasang
        
        # Petakan warna relic yang sudah kita pasang saat ini
        equipped_colors: Set[str] = set()
        for r_type in equipped_relic_types:
            if r_type in ITEM_DATABASE:
                equipped_colors.add(ITEM_DATABASE[r_type].get("slot_color", ""))

        # Jika kita belum memiliki 3 relic terpasang, coba cari relic di tas dengan warna yang belum kita miliki [9]
        if len(equipped_colors) < 3:
            for item in inventory_items:
                item_id = item.get("id", "")
                item_type = item.get("type", "")

                if item_type in ITEM_DATABASE:
                    info = ITEM_DATABASE[item_type]
                    if info.get("category") == "relic":
                        color = info.get("slot_color", "")
                        # Pasang relic jika warnanya belum ada di slot aktif saat ini untuk mengejar fullSet [9]
                        if color not in equipped_colors:
                            # Cari indeks slot kosong (1, 2, atau 3) yang bisa kita gunakan
                            slot_name = f"relic_{len(equipped_colors) + 1}"
                            return item_id, slot_name

        return None