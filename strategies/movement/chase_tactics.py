# -*- coding: utf-8 -*-
"""
ClawRoyale Hunter Chase Tactics.
Calculates interception routes to cut off fleeing targets and optimize attack placement [11].
"""

from typing import Dict, Any, Tuple, Optional, List
from core.state.game_state import GameState
from utils.math_helper import calculate_hex_distance
from config.item_registry import ITEM_DATABASE
from strategies.movement.pathfinder import HEX_NEIGHBORS


class ChaseTactics:
    def __init__(self, game_state: GameState):
        self.game_state = game_state

    def predict_target_next_position(self, current_target_coord: Tuple[int, int], 
                                     previous_target_coord: Optional[Tuple[int, int]]) -> Tuple[int, int]:
        """
        Predicts the target's next step based on their heading vector.
        """
        if not previous_target_coord:
            # Jika tidak ada riwayat, asumsikan target diam turn ini
            return current_target_coord

        tq, tr = current_target_coord
        pq, pr = previous_target_coord

        # Hitung arah vektor pergerakan musuh
        dq = tq - pq
        dr = tr - pr

        # Batasi agar prediksi pergerakan maksimal 1 kotak heksagonal
        pred_q = tq + max(-1, min(1, dq))
        pred_r = tr + max(-1, min(1, dr))

        return (pred_q, pred_r)

    def calculate_interception_hex(self, target_coord: Tuple[int, int], 
                                    previous_target_coord: Optional[Tuple[int, int]]) -> Tuple[int, int]:
        """
        Calculates the optimal coordinate to intercept the target.
        Adjusts based on whether we hold a melee (range 0) or ranged weapon (range 1-2) [11].
        """
        predicted_target_pos = self.predict_target_next_position(target_coord, previous_target_coord)
        bot_pos = (self.game_state.q, self.game_state.r)

        # 1. Ambil jarak serang optimal senjata bot kita [9, 11]
        my_weapon_id = self.game_state.equipped_weapon
        optimal_range = 0
        if my_weapon_id in ITEM_DATABASE:
            optimal_range = int(ITEM_DATABASE[my_weapon_id].get("range", 0))

        # Skenario 1: Senjata melee -> Target intersepsi adalah tepat menempel di koordinat target
        if optimal_range == 0:
            return predicted_target_pos

        # Skenario 2: Senjata ranged -> Intersepsi di koordinat berjarak 1-2 hex dari target [11]
        best_intercept_coord = predicted_target_pos
        min_dist_to_bot = 9999

        pq, pr = predicted_target_pos

        # Evaluasi semua tetangga heksagonal di sekitar prediksi koordinat target
        for dq, dr in HEX_NEIGHBORS:
            neighbor = (pq + dq, pr + dr)
            dist_to_predicted_target = calculate_hex_distance(neighbor, predicted_target_pos)
            
            # Pastikan titik intersepsi berada di jarak optimal senjata ranged kita (jarak 1 atau 2) [11]
            if dist_to_predicted_target <= optimal_range:
                dist_to_bot = calculate_hex_distance(neighbor, bot_pos)
                if dist_to_bot < min_dist_to_bot:
                    min_dist_to_bot = dist_to_bot
                    best_intercept_coord = neighbor

        return best_intercept_coord