# -*- coding: utf-8 -*-
"""
ClawRoyale Hexagonal A* Pathfinder.
Computes optimal movement paths while avoiding obstacles, slow terrains, and Dead Zones [14].
"""

import heapq
from typing import Dict, Any, List, Tuple, Set, Optional
from core.state.game_state import GameState
from utils.math_helper import calculate_hex_distance
from config.game_constants import TERRAIN_MODIFIERS

HEX_NEIGHBORS = [
    (1, 0), (1, -1), (0, -1),
    (-1, 0), (-1, 1), (0, 1)
]


class HexPathfinder:
    def __init__(self, game_state: GameState):
        self.game_state = game_state

    def _get_neighbors(self, coord: Tuple[int, int]) -> List[Tuple[int, int]]:
        q, r = coord
        return [(q + dq, r + dr) for dq, dr in HEX_NEIGHBORS]

    def _calculate_tile_cost(self, coord: Tuple[int, int], deadzone_coords: Set[Tuple[int, int]]) -> float:
        """
        Calculates the traversal cost of a hex tile.
        Applies multipliers for slow terrain and huge penalties for Dead Zone coordinates [14].
        """
        if coord in deadzone_coords:
            return 999.0

        terrain_type = self.game_state.current_terrain
        modifier = TERRAIN_MODIFIERS.get(terrain_type, {})
        
        ep_multiplier = float(modifier.get("ep_cost_multiplier", 1.0))
        return 1.0 * ep_multiplier

    def find_path(self, start: Tuple[int, int], target: Tuple[int, int], 
                  blocked_coords: Set[Tuple[int, int]], 
                  deadzone_coords: Set[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Finds the shortest, safest path from start to target coordinate using A* on a hex grid.
        """
        if start == target:
            return []

        open_set: List[Tuple[float, Tuple[int, int]]] = []
        heapq.heappush(open_set, (0.0, start))

        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score: Dict[Tuple[int, int], float] = {start: 0.0}
        f_score: Dict[Tuple[int, int], float] = {
            start: float(calculate_hex_distance(start, target))
        }

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == target:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path

            for neighbor in self._get_neighbors(current):
                if neighbor in blocked_coords:
                    continue

                step_cost = self._calculate_tile_cost(neighbor, deadzone_coords)
                tentative_g_score = g_score[current] + step_cost

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    
                    h_score = float(calculate_hex_distance(neighbor, target))
                    f_score[neighbor] = tentative_g_score + h_score
                    
                    if not any(item[1] == neighbor for item in open_set):
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return []