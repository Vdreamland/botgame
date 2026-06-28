# -*- coding: utf-8 -*-
"""
ClawRoyale Enemy Cooldown and Energy Tracker.
Estimates enemy action availability (30s cooldowns) and remaining EP [12].
"""

import time
from typing import Dict, Any


class EnemyCooldownTracker:
    def __init__(self):
        # Struktur: { player_id: { "last_action_time": float, "estimated_ep": float } }
        self._tracked_enemies: Dict[str, Dict[str, Any]] = {}

    def track_enemy_action(self, player_id: str, action_type: str, terrain_ep_multiplier: float = 1.0) -> None:
        """
        Records when an enemy executes a cooldown action to calculate their local lock [12].
        """
        now = time.monotonic()
        
        # Inisialisasi jika musuh belum terdaftar
        if player_id not in self._tracked_enemies:
            self._tracked_enemies[player_id] = {
                "last_action_time": 0.0,
                "estimated_ep": 30.0
            }

        entry = self._tracked_enemies[player_id]
        
        # Aksi ber-cooldown mengaktifkan lock 30 detik [12]
        if action_type in ["move", "attack", "explore", "rest", "interact"]:
            entry["last_action_time"] = now

        # Estimasi pengurangan EP musuh secara dinamis
        if action_type == "move":
            # Pergerakan mengonsumsi energi dasar dikalikan dengan multiplier terrain
            entry["estimated_ep"] = max(0.0, entry["estimated_ep"] - (2.0 * terrain_ep_multiplier))
        elif action_type == "attack":
            entry["estimated_ep"] = max(0.0, entry["estimated_ep"] - 4.0)
        elif action_type == "rest":
            # Rest memulihkan EP musuh secara instan
            entry["estimated_ep"] = min(30.0, entry["estimated_ep"] + 15.0)

    def is_enemy_locked_in_cooldown(self, player_id: str) -> bool:
        """
        Checks if the enemy is currently waiting for their 30-second action cooldown to expire [12].
        """
        entry = self._tracked_enemies.get(player_id)
        if not entry:
            return False

        elapsed = time.monotonic() - entry["last_action_time"]
        return elapsed < 30.0

    def get_estimated_enemy_ep(self, player_id: str) -> float:
        """
        Returns estimated remaining Energy Points of the enemy player.
        """
        entry = self._tracked_enemies.get(player_id)
        if not entry:
            return 30.0  # Asumsikan EP penuh jika belum terdeteksi
        return entry["estimated_ep"]

    def clean_dead_enemies(self, active_enemy_ids: list) -> None:
        """
        Cleans up memory by removing enemies that are no longer in the game.
        """
        for pid in list(self._tracked_enemies.keys()):
            if pid not in active_enemy_ids:
                self._tracked_enemies.pop(pid, None)