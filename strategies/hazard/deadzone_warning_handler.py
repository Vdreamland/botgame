# -*- coding: utf-8 -*-
"""
ClawRoyale Dead Zone Warning Handler.
Plans safe routes to the center coordinates before the Death Zone expands [14].
"""

from typing import Tuple, List, Set
from core.state.game_state import GameState
from strategies.movement.pathfinder import HexPathfinder


class DeadZoneWarningHandler:
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.pathfinder = HexPathfinder(game_state)

    def is_warning_active(self) -> bool:
        """
        Returns True if the current day/turn indicates the Dead Zone is about to expand [14].
        - Expansion starts on Day 2, occurring every 3 turns.
        """
        day = self.game_state.day
        turn = self.game_state.turn

        if day >= 2 and (turn % 3 == 0):
            return True
        return False

    def calculate_evacuation_path(self, safe_center_coord: Tuple[int, int], 
                                  blocked_coords: Set[Tuple[int, int]], 
                                  active_deadzone_coords: Set[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Pre-computes the optimal escape path to the designated safe zone coordinates.
        """
        bot_pos = (self.game_state.q, self.game_state.r)
        
        # Panggil pathfinder untuk menyusun rute evakuasi dini
        return self.pathfinder.find_path(
            start=bot_pos,
            target=safe_center_coord,
            blocked_coords=blocked_coords,
            deadzone_coords=active_deadzone_coords
        )