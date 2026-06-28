# -*- coding: utf-8 -*-
"""
ClawRoyale Dead Zone Warning Handler.
Plans safe routes to the center region before the Death Zone expands [14].
"""

from typing import List, Set, Union, Tuple
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

    def calculate_evacuation_path(self, safe_center: Union[str, Tuple[int, int]], 
                                  blocked_coords: Set[Union[str, Tuple[int, int]]], 
                                  active_deadzone_coords: Set[Union[str, Tuple[int, int]]]) -> List[Union[str, Tuple[int, int]]]:
        """
        Pre-computes the optimal escape path to the designated safe zone region ID or coordinate.
        Supports both string region IDs and legacy coordinate tuples.
        """
        if isinstance(safe_center, str):
            bot_pos = self.game_state.current_region_id
            return self.pathfinder.find_path(
                start=bot_pos,
                target=safe_center,
                blocked_coords=blocked_coords,
                deadzone_coords=active_deadzone_coords
            )

        # Fallback legacy coordinates
        bot_pos_coord = (self.game_state.q, self.game_state.r)
        return self.pathfinder.find_path(
            start=bot_pos_coord,
            target=safe_center,
            blocked_coords=blocked_coords,
            deadzone_coords=active_deadzone_coords
        )