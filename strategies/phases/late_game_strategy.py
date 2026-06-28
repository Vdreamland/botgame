# -*- coding: utf-8 -*-
"""
ClawRoyale Late Game Strategy.
Focuses entirely on stealth survival, defensive forest positioning, and conserving EP.
"""

from typing import Dict, Any, Optional, Tuple
from core.state.game_state import GameState
from config.game_constants import TERRAIN_MODIFIERS


class LateGameStrategy:
    def __init__(self, game_state: GameState):
        self.game_state = game_state

    def determine_late_action(self, enemies_count: int) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Enforces defensive and protective late-game survival tactics.
        """
        # 1. Prioritas Utama: Cari area Forest (+3.0 DEF) di sekitar jika saat ini tidak berdiri di Forest
        current_terrain = self.game_state.current_terrain.lower()
        
        if current_terrain != "forest" and self.game_state.ep >= 10.0:
            # Sinyal untuk berpindah mencari Forest heksagonal terdekat
            return "MOVE_TO_FOREST", None

        # 2. Prioritas Kedua: Jika EP di bawah 20 dan tidak ada ancaman musuh, lakukan REST untuk menghemat energi
        if self.game_state.ep < 20.0 and enemies_count == 0:
            return "CONSERVE_REST", None

        # 3. Default: Bertahan pasif di tempat (Hold Ground)
        return "DEFENSIVE_HOLD", None