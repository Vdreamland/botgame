# -*- coding: utf-8 -*-
"""
ClawRoyale Dead Zone Emergency Active Handler.
Overrides all decisions to force immediate escape from active Death Zones (1.34 HP/s) [14].
"""

from typing import Tuple, List, Set, Optional, Any
from core.state.game_state import GameState
from strategies.movement.pathfinder import HexPathfinder
from strategies.recovery.health_restorer import HealthRestorer


class DeadZoneActiveHandler:
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.pathfinder = HexPathfinder(game_state)
        self.health_restorer = HealthRestorer(game_state)

    def is_in_danger(self) -> bool:
        """
        Checks if the agent's current coordinate is inside the active Death Zone [14].
        """
        return self.game_state.is_death_zone

    def determine_emergency_response(self, safe_escape_coord: Tuple[int, int], 
                                     blocked_coords: Set[Tuple[int, int]], 
                                     active_deadzone_coords: Set[Tuple[int, int]]) -> Tuple[str, Optional[Any]]:
        """
        Calculates the immediate escape action.
        Prioritizes: Emergency auto-healing while executing movement steps to stay alive [14].
        :return: Tuple[emergency_action_type, details_data]
        """
        # 1. Cek Kelayakan Medis Darurat: Jika HP bot berkurang banyak, gunakan obat penyembuh terlebih dahulu
        healing_item = self.health_restorer.determine_healing_action()
        if healing_item and self.game_state.hp < 60.0:
            # Gunakan item medis instan (Free Action) untuk mengompensasi damage 1.34 HP/s [14]
            return "EMERGENCY_HEAL", healing_item

        # 2. Hitung Jalur Evakuasi Tercepat menuju koordinat aman terdekat
        bot_pos = (self.game_state.q, self.game_state.r)
        escape_path = self.pathfinder.find_path(
            start=bot_pos,
            target=safe_escape_coord,
            blocked_coords=blocked_coords,
            deadzone_coords=active_deadzone_coords
        )

        if escape_path:
            # Ambil koordinat langkah berikutnya di jalur evakuasi
            next_step = escape_path[0]
            return "EMERGENCY_MOVE", next_step

        return "EMERGENCY_STUCK_REST", None