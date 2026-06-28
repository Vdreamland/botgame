# -*- coding: utf-8 -*-
"""
ClawRoyale Graph/Region BFS Pathfinder.
Computes optimal movement paths over region connections while avoiding Dead Zones [14].
"""

from typing import Dict, Any, List, Set, Optional, Tuple
from core.state.game_state import GameState


class HexPathfinder:
    """
    Dipertahankan dengan nama kelas HexPathfinder agar kompatibel dengan modul impor lain
    tanpa merusak sistem, namun mengimplementasikan pencarian jalan berbasis graf BFS di dalamnya.
    """
    def __init__(self, game_state: GameState):
        self.game_state = game_state

    def find_path(self, start: str, target: str, 
                  blocked_coords: Set[str], 
                  deadzone_coords: Set[str]) -> List[str]:
        """
        Mencari daftar rute ID wilayah terpendek dari wilayah start ke target menggunakan BFS.
        """
        if start == target:
            return []

        # Antrean (queue) berisi (current_region, path_so_far)
        queue: List[Tuple[str, List[str]]] = [(start, [])]
        visited: Set[str] = {start}

        while queue:
            current, path = queue.pop(0)

            if current == target:
                return path

            # Tentukan tetangga/koneksi aktif dari GameState
            neighbors = []
            if current == self.game_state.current_region_id:
                neighbors = self.game_state.connections
            else:
                for r in self.game_state.visible_ruins:
                    if r.get("ruinId") == target:
                        neighbors = [target]
                        break

            for neighbor in neighbors:
                if neighbor in visited or neighbor in deadzone_coords:
                    continue

                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

        # Pengaman/fallback jika target ada di dekat tapi tidak terdaftar di connections
        for r in self.game_state.visible_ruins:
            if r.get("ruinId") == target and target in self.game_state.connections:
                return [target]

        return []