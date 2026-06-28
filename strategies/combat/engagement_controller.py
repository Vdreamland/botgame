# -*- coding: utf-8 -*-
"""
ClawRoyale Combat Engagement Controller.
Determines spatial tactics based on weapon ranges (Melee vs Ranged) [11].
"""

from typing import Dict, Any, Tuple
from config.item_registry import ITEM_DATABASE
from core.state.game_state import GameState


class EngagementController:
    def __init__(self, game_state: GameState):
        self.game_state = game_state

    def determine_spatial_tactic(self, target_data: Dict[str, Any], 
                                  distance: int) -> Tuple[str, Dict[str, Any]]:
        """
        Analyzes weapon range advantages and recommends the next physical action.
        :param target_data: Target enemy dictionary.
        :param distance: Hexagonal distance to the target.
        :return: Tuple[tactic_string, details_dict]
        
        Tactics:
        - "ATTACK": Target is perfectly within our weapon range.
        - "APPROACH": Target is too far, need to close the gap.
        - "RETREAT_TO_RANGE": Target is too close (melee range 0) while we hold a ranged weapon (range 1-2).
        - "REST": We need to attack or move but our EP is too low.
        """
        # 1. Ambil data senjata bot kita saat ini [9, 11]
        my_weapon_id = self.game_state.equipped_weapon
        my_range = 0
        my_ep_cost = 3.0

        if my_weapon_id in ITEM_DATABASE:
            w_info = ITEM_DATABASE[my_weapon_id]
            my_range = int(w_info.get("range", 0))
            my_ep_cost = float(w_info.get("ep_usage", 3.0))

        # 2. Cek apakah EP bot kita cukup untuk melakukan aksi penyerangan
        if self.game_state.ep < my_ep_cost:
            return "REST", {"reason": "Insufficient EP to execute attack."}

        # 3. Klasifikasi Taktis Berdasarkan Jarak Heksagonal [11]
        if my_range == 0:
            # --- SENJATA MELEE (Sword/Blade) ---
            if distance == 0:
                # Sudah menempel, lakukan serangan
                return "ATTACK", {"action": "attack"}
            else:
                # Musuh berada di luar jangkauan melee, harus mendekat
                return "APPROACH", {"target_coords": (target_data.get("q"), target_data.get("r"))}
                
        else:
            # --- SENJATA RANGED (Rifle/Bow) [11] ---
            if distance == 0:
                # Bahaya: Musuh menempel (jarak 0) sedangkan kita memegang senjata ranged.
                # Mundur 1 langkah ke koordinat aman untuk mengembalikan keunggulan jarak 1-2 [11].
                return "RETREAT_TO_RANGE", {
                    "reason": "Target entered melee range. Retreating to optimize ranged advantage."
                }
            elif 1 <= distance <= my_range:
                # Musuh berada di jarak optimal (1 atau 2 hex), lakukan tembakan [11].
                return "ATTACK", {"action": "attack"}
            else:
                # Musuh terlalu jauh, harus mendekat hingga menyentuh jarak optimal [11].
                return "APPROACH", {"target_coords": (target_data.get("q"), target_data.get("r"))}