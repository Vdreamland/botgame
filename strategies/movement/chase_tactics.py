# -*- coding: utf-8 -*-
"""
ClawRoyale Hunter Chase Tactics.
Calculates interception routes to cut off fleeing targets and optimize attack placement [11].
"""

from typing import Dict, Any, Tuple, Optional, List, Union
from core.state.game_state import GameState
from config.item_registry import ITEM_DATABASE


class ChaseTactics:
    def __init__(self, game_state: GameState):
        self.game_state = game_state

    def predict_target_next_position(self, current_target: Union[str, Tuple[int, int]], 
                                     previous_target: Optional[Union[str, Tuple[int, int]]] = None) -> Union[str, Tuple[int, int]]:
        """
        Predicts the target's next step based on heading vectors.
        Supports both Graph-based region IDs and legacy hexagonal coordinates.
        """
        # Skenario 1: Jika input berupa ID Wilayah (Region ID) Graf
        if isinstance(current_target, str):
            return current_target

        # Skenario 2: Jika input berupa koordinat heksagonal legacy (q, r)
        if not previous_target or not isinstance(previous_target, tuple):
            return current_target

        tq, tr = current_target
        pq, pr = previous_target

        # Hitung arah vektor pergerakan musuh
        dq = tq - pq
        dr = tr - pr

        # Batasi agar prediksi pergerakan maksimal 1 kotak heksagonal
        pred_q = tq + max(-1, min(1, dq))
        pred_r = tr + max(-1, min(1, dr))

        return (pred_q, pred_r)

    def calculate_interception_hex(self, target: Union[str, Tuple[int, int]], 
                                    previous_target: Optional[Union[str, Tuple[int, int]]] = None) -> Union[str, Tuple[int, int]]:
        """
        Calculates the optimal coordinate or region ID to intercept the target.
        Adapts based on whether we hold a melee (range 0) or ranged weapon (range 1-2) [11].
        """
        # Skenario 1: Jika input berupa ID Wilayah (Region ID) Graf
        if isinstance(target, str):
            return target

        # Skenario 2: Jika input berupa koordinat heksagonal legacy (q, r)
        predicted_target_pos = self.predict_target_next_position(target, previous_target)
        if isinstance(predicted_target_pos, str):
            return predicted_target_pos

        bot_pos = (self.game_state.q, self.game_state.r)

        # 1. Ambil Jangkauan Senjata Bot kita
        my_weapon_id = self.game_state.equipped_weapon
        optimal_range = 0
        if my_weapon_id in ITEM_DATABASE:
            optimal_range = int(ITEM_DATABASE[my_weapon_id].get("range", 0))

        # Senjata melee -> Target intersepsi adalah tepat menempel di koordinat target
        if optimal_range == 0:
            return predicted_target_pos

        # Senjata ranged -> Intersepsi langsung di koordinat prediksi target
        return predicted_target_pos