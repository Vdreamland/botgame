# -*- coding: utf-8 -*-
"""
ClawRoyale Enemy Stats Scanner.
Extracts vital statistics (HP, EP) of a targeted hostile player.
"""

from typing import Dict, Any


class EnemyStatsScanner:
    @staticmethod
    def extract_vital_stats(enemy_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Parses dynamic health and energy points of the targeted enemy.
        """
        hp = float(enemy_data.get("hp", 100.0))
        ep = float(enemy_data.get("ep", 30.0))
        max_hp = float(enemy_data.get("maxHp", 100.0))
        max_ep = float(enemy_data.get("maxEp", 30.0))

        # Rasio sisa kesehatan
        hp_ratio = hp / max_hp if max_hp > 0 else 1.0

        return {
            "hp": hp,
            "max_hp": max_hp,
            "hp_ratio": hp_ratio,
            "ep": ep,
            "max_ep": max_ep
        }

    @staticmethod
    def is_enemy_exhausted(enemy_data: Dict[str, Any]) -> bool:
        """
        Detects if the enemy has run out of Energy Points (EP).
        Exhausted enemies cannot run or execute high-cost counterattacks.
        """
        ep = float(enemy_data.get("ep", 30.0))
        return ep < 5.0