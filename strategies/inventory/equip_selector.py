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

        # Ambil status serangan senjata terpasang saat ini secara case-insensitive [11]
        current_weapon_type = self.game_state.equipped_weapon
        
        # PENGAMAN MUTLAK: Hanya proses jika bot terbukti memegang senjata (bukan None atau string kosong)
        if current_weapon_type:
            normalized_current_weapon = current_weapon_type.lower().replace("_", " ").strip()
            matched_current_weapon_info = None
            
            for db_key, db_info in ITEM_DATABASE.items():
                if db_key.lower().replace("_", " ").strip() == normalized_current_weapon:
                    matched_current_weapon_info = db_info
                    break

            if matched_current_weapon_info:
                highest_weapon_atk = float(matched_current_weapon_info.get("atk_bonus", 0.0))
        
        # Jika tidak ada senjata terpasang atau tidak dikenali, highest_weapon_atk tetap 0.0

        for item in inventory_items:
            item_id = item.get("id") or item.get("itemId") or ""
            item_type = item.get("type", "")

            # Cari info di database secara case-insensitive
            normalized_search = item_type.lower().replace("_", " ").strip()
            matched_info = None
            for db_key, db_info in ITEM_DATABASE.items():
                if db_key.lower().replace("_", " ").strip() == normalized_search:
                    matched_info = db_info
                    break

            if matched_info:
                if matched_info.get("category") == "weapon":
                    atk_bonus = float(matched_info.get("atk_bonus", 0.0))
                    # Jika menemukan senjata dengan serangan lebih tinggi, jadikan target pasang [11]
                    if atk_bonus > highest_weapon_atk:
                        highest_weapon_atk = atk_bonus
                        best_weapon_id = item_id

        if best_weapon_id:
            return best_weapon_id, "weapon"

        # 2. OPTIMALISASI RELIC (MENGEJAR BONUS fullSet RGB) [9]
        equipped_relic_types = self.game_state.equipped_relics  # List tipe relic yang terpasang
        
        # Petakan warna relic yang sudah kita pasang saat ini secara case-insensitive
        equipped_colors: Set[str] = set()
        for r_type in equipped_relic_types:
            # PENGAMAN MUTLAK: Hanya proses jika relic terbukti ada (bukan None atau string kosong)
            if r_type:
                normalized_r = r_type.lower().replace("_", " ").strip()
                matched_relic_info = None
                for db_key, db_info in ITEM_DATABASE.items():
                    if db_key.lower().replace("_", " ").strip() == normalized_r:
                        matched_relic_info = db_info
                        break

                if matched_relic_info:
                    color = matched_relic_info.get("slot_color", "")
                    if color:
                        equipped_colors.add(color.lower())

        # Coba pasang relic di tas dengan warna yang belum kita miliki [9]
        if len(equipped_colors) < 3:
            for item in inventory_items:
                item_id = item.get("id") or item.get("itemId") or ""
                item_type = item.get("type", "")

                normalized_search = item_type.lower().replace("_", " ").strip()
                matched_info = None
                for db_key, db_info in ITEM_DATABASE.items():
                    if db_key.lower().replace("_", " ").strip() == normalized_search:
                        matched_info = db_info
                        break

                if matched_info:
                    if matched_info.get("category") == "relic":
                        color = matched_info.get("slot_color", "")
                        if color:
                            normalized_color = color.lower()
                            # Pasang relic jika warnanya belum ada di slot aktif saat ini untuk mengejar fullSet [9]
                            if normalized_color not in equipped_colors:
                                # Cari indeks slot kosong (1, 2, atau 3) yang bisa kita gunakan
                                slot_name = f"relic_{len(equipped_colors) + 1}"
                                return item_id, slot_name

        return None