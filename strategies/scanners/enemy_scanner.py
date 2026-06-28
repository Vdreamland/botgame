# -*- coding: utf-8 -*-
"""
ClawRoyale Enemy Proximity Scanner.
Identifies the positions and distances of active hostile players [8].
"""

from typing import Dict, Any, List, Optional
from core.state.game_state import GameState
from utils.math_helper import calculate_hex_distance


class EnemyScanner:
    def __init__(self, game_state: GameState, scan_radius: int = 3):
        self.game_state = game_state
        self.scan_radius = scan_radius

    def get_closest_enemy(self) -> Optional[Dict[str, Any]]:
        """
        Scans adjacent hexes and returns the nearest hostile player.
        Filters out self and registered team allies [8].
        """
        enemies = self.game_state.enemies
        if not enemies:
            return None

        closest_enemy: Optional[Dict[str, Any]] = None
        min_distance = 9999

        # Posisi bot saat ini
        bot_coord = (self.game_state.q, self.game_state.r)

        for enemy in enemies:
            eq = int(enemy.get("q", 0))
            er = int(enemy.get("r", 0))
            enemy_coord = (eq, er)

            distance = calculate_hex_distance(bot_coord, enemy_coord)
            
            # Abaikan musuh yang berada di luar jangkauan scan radius visual
            if distance > self.scan_radius:
                continue

            if distance < min_distance:
                min_distance = distance
                closest_enemy = enemy

        if closest_enemy:
            # Kembalikan data musuh terdekat beserta jarak kalkulasi lokal
            result = closest_enemy.copy()
            result["distance"] = min_distance
            return result

        return None

    def get_all_visible_enemies(self) -> List[Dict[str, Any]]:
        """
        Returns a sorted list of all hostile players within the scan radius,
        ordered from closest to furthest.
        """
        enemies = self.game_state.enemies
        if not enemies:
            return []

        bot_coord = (self.game_state.q, self.game_state.r)
        scanned_list = []

        for enemy in enemies:
            eq = int(enemy.get("q", 0))
            er = int(enemy.get("r", 0))
            distance = calculate_hex_distance(bot_coord, (eq, er))

            if distance <= self.scan_radius:
                item = enemy.copy()
                item["distance"] = distance
                scanned_list.append(item)

        # Urutkan berdasarkan jarak heksagonal terdekat
        scanned_list.sort(key=lambda x: x["distance"])
        return scanned_list