# -*- coding: utf-8 -*-
"""
ClawRoyale Enemy Proximity Scanner.
Identifies the positions and distances of active hostile players [8].
"""

from typing import Dict, Any, List, Optional
from core.state.game_state import GameState


class EnemyScanner:
    def __init__(self, game_state: GameState, scan_radius: int = 3):
        self.game_state = game_state
        self.scan_radius = scan_radius

    def get_closest_enemy(self) -> Optional[Dict[str, Any]]:
        """
        Scans adjacent regions and returns the nearest hostile player.
        Filters out self and registered team allies [8].
        """
        enemies = self.game_state.enemies
        if not enemies:
            return None

        closest_enemy: Optional[Dict[str, Any]] = None
        min_distance = 9999

        bot_region = self.game_state.current_region_id

        for enemy in enemies:
            enemy_region = enemy.get("regionId") or self.game_state.current_region_id
            
            # Hitung jarak berbasis wilayah graf (0 = wilayah sama, 1 = bersebelahan, 2 = lebih jauh)
            if enemy_region == bot_region:
                distance = 0
            elif enemy_region in self.game_state.connections:
                distance = 1
            else:
                distance = 2

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

        bot_region = self.game_state.current_region_id
        scanned_list = []

        for enemy in enemies:
            enemy_region = enemy.get("regionId") or self.game_state.current_region_id
            
            if enemy_region == bot_region:
                distance = 0
            elif enemy_region in self.game_state.connections:
                distance = 1
            else:
                distance = 2

            if distance <= self.scan_radius:
                item = enemy.copy()
                item["distance"] = distance
                scanned_list.append(item)

        # Urutkan berdasarkan jarak terdekat
        scanned_list.sort(key=lambda x: x["distance"])
        return scanned_list