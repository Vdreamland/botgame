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
        Analyzes weapon range advantages and recommends next action based on Region-Hop distance.
        :param target_data: Target enemy dictionary.
        :param distance: Region hop distance to the target (0 = same region, 1 = adjacent).
        :return: Tuple[tactic_string, details_dict]
        """
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

        # 3. Klasifikasi Taktis Berdasarkan Region Hop (0 = same region, 1 = adjacent)
        if my_range == 0:
            # --- Melee ---
            if distance == 0:
                return "ATTACK", {"action": "attack"}
            else:
                return "APPROACH", {"target_coords": target_data.get("regionId")}
        else:
            # --- Ranged ---
            if distance == 0:
                # Mundur ke wilayah tetangga untuk mengembalikan optimal range 1
                return "RETREAT_TO_RANGE", {"reason": "Retreating to adjacent region to shoot."}
            elif distance == 1:
                return "ATTACK", {"action": "attack"}
            else:
                return "APPROACH", {"target_coords": target_data.get("regionId")}