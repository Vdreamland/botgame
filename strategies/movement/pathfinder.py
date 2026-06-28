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

# Pergeseran koordinat tetangga pada koordinat axial heksagonal (q, r) [8]
HEX_NEIGHBORS = [
    (1, 0), (1, -1), (0, -1),
    (-1, 0), (-1, 1), (0, 1)
]


class HexPathfinder:
    def __init__(self, game_state: GameState):
        self.game_state = game_state

    def _get_neighbors(self, coord: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Returns all 6 adjacent hexagonal coordinates.
        """
        q, r = coord
        return [(q + dq, r + dr) for dq, dr in HEX_NEIGHBORS]

    def _calculate_tile_cost(self, coord: Tuple[int, int], deadzone_coords: Set[Tuple[int, int]]) -> float:
        """
        Calculates the traversal cost of a hex tile.
        Applies multipliers for slow terrain and huge penalties for Dead Zone coordinates [14].
        """
        # Skenario 1: Koordinat berada di dalam Dead Zone (Beri penalti sangat tinggi) [14]
        if coord in deadzone_coords:
            return 999.0

        # Skenario 2: Koordinat berada di dalam area terrain khusus
        # Pada pengerjaan real-time, kita mengasumsikan terrain dibaca dari database lokal game_state
        terrain_type = self.game_state.current_terrain
        modifier = TERRAIN_MODIFIERS.get(terrain_type, {})
        
        # Ambil multiplier konsumsi energi (EP cost)
        ep_multiplier = float(modifier.get("ep_cost_multiplier", 1.0))
        
        # Biaya dasar bergerak adalah 1.0 EP dikali multiplier terrain
        return 1.0 * ep_multiplier

    def find_path(self, start: Tuple[int, int], target: Tuple[int, int], 
                  blocked_coords: Set[Tuple[int, int]], 
                  deadzone_coords: Set[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Finds the shortest, safest path from start to target coordinate using A* on a hex grid.
        :param start: Starting coordinate (q, r).
        :param target: Destination coordinate (q, r).
        :param blocked_coords: Coordinates of hard obstacles (e.g. ruins walls).
        :param deadzone_coords: Coordinates currently engulfed by the Dead Zone [14].
        :return: List of coordinates representing the path (excluding start, including target).
        """
        if start == target:
            return []

        # Antrean prioritas (Priority Queue): (f_score, current_node)
        open_set: List[Tuple[float, Tuple[int, int]]] = []
        heapq.heappush(open_set, (0.0, start))

        # Pencatat jalur kembali (node induk)
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}

        # g_score: biaya terkecil nyata dari start ke node tersebut
        g_score: Dict[Tuple[int, int], float] = {start: 0.0}

        # f_score: perkiraan total biaya dari start ke target melalui node tersebut (g_score + heuristic)
        f_score: Dict[Tuple[int, int], float] = {
            start: float(calculate_hex_distance(start, target))
        }

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == target:
                # Rekonstruksi jalur kembali dari target ke start
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path

            for neighbor in self._get_neighbors(current):
                # Abaikan jika koordinat tetangga adalah rintangan mati (tembok)
                if neighbor in blocked_coords:
                    continue

                # Hitung biaya nyata untuk melangkah ke tetangga ini
                step_cost = self._calculate_tile_cost(neighbor, deadzone_coords)
                tentative_g_score = g_score[current] + step_cost

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    
                    # Heuristic menggunakan rumus jarak heksagonal murni
                    h_score = float(calculate_hex_distance(neighbor, target))
                    f_score[neighbor] = tentative_g_score + h_score
                    
                    # Tambahkan ke open set jika belum terdaftar
                    if not any(item[1] == neighbor for item in open_set):
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))

        # Tidak ada rute aman yang ditemukan (kembalikan jalur kosong)
        return []