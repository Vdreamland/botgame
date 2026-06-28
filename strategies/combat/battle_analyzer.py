# -*- coding: utf-8 -*-
"""
ClawRoyale Combat Threat Analyzer.
Integrates target scanning and simulations to determine safe combat actions [11].
"""

from typing import Dict, Any, Optional
from core.state.game_state import GameState
from config.settings import AI_SETTINGS
from strategies.scanners.enemy_scanner import EnemyScanner
from strategies.scanners.enemy_stats_scanner import EnemyStatsScanner
from strategies.scanners.enemy_gear_scanner import EnemyGearScanner
from strategies.combat.victory_calculator import VictoryCalculator


class BattleAnalyzer:
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.scanner = EnemyScanner(game_state, scan_radius=AI_SETTINGS["scan_radius_enemies"])

    def evaluate_combat_situation(self) -> Dict[str, Any]:
        """
        Inspects the nearest enemy threat and simulates the fight.
        Returns a dictionary recommending the safest state: 'FIGHT', 'FLEE', or 'STANDBY'.
        """
        closest_enemy = self.scanner.get_closest_enemy()
        if not closest_enemy:
            # Tidak ada musuh di sekitar radius visual bot
            return {
                "recommendation": "STANDBY",
                "target": None,
                "win_rate": 0.0,
                "distance": 999
            }

        distance = closest_enemy["distance"]
        enemy_id = closest_enemy.get("id", "")

        # 1. Scan Status Vital & Persenjataan Musuh [11]
        enemy_vitals = EnemyStatsScanner.extract_vital_stats(closest_enemy)
        enemy_combat_stats = EnemyGearScanner.calculate_effective_combat_stats(closest_enemy)

        # 2. Ambil Statistik Efektif Milik Bot Kita Saat Ini [9, 11]
        my_relics = self.game_state.equipped_relics
        my_combat_stats = EnemyGearScanner.calculate_effective_combat_stats({
            "loadout": {
                "weapon": self.game_state.equipped_weapon,
                "armor": self.game_state.equipped_armor,
                "relics": my_relics,
                "fullSet": self.game_state.has_full_set
            }
        })

        # 3. Jalankan Kalkulasi Simulasi Turn-Based [11]
        win_rate = VictoryCalculator.simulate_battle_outcome(
            my_stats=my_combat_stats,
            enemy_stats=enemy_combat_stats,
            my_current_hp=self.game_state.hp,
            enemy_current_hp=enemy_vitals["hp"]
        )

        # 4. Formulasi Keputusan Berdasarkan Threshold Pengaturan setting.py
        min_fight_rate = AI_SETTINGS["min_win_rate_for_aggression"]
        flee_rate = AI_SETTINGS["flee_win_rate_threshold"]

        if win_rate >= min_fight_rate:
            recommendation = "FIGHT"
        elif win_rate < flee_rate:
            recommendation = "FLEE"
        else:
            # Berada di zona abu-abu: Bersiap siaga (bertahan atau jaga jarak)
            recommendation = "STANDBY"

        return {
            "recommendation": recommendation,
            "target": closest_enemy,
            "win_rate": win_rate,
            "distance": distance
        }