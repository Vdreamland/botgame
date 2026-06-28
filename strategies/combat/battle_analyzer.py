# -*- coding: utf-8 -*-
"""
ClawRoyale Combat Threat Analyzer.
Integrates target scanning and simulations to determine safe combat actions [11].
"""

from typing import Dict, Any, Optional
from core.state.game_state import GameState
from config.settings import AI_SETTINGS
from strategies.scanners.enemy_scanner import EnemyScanner
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
            return {
                "recommendation": "STANDBY",
                "target": None,
                "win_rate": 0.0,
                "distance": 999
            }

        # Hitung jarak Hops sesungguhnya berbasis wilayah Graf (0 = ubin sama, 1 = tetangga, 2 = jauh)
        enemy_region = closest_enemy.get("regionId") or self.game_state.current_region_id
        if enemy_region == self.game_state.current_region_id:
            distance = 0
        elif enemy_region in self.game_state.connections:
            distance = 1
        else:
            distance = 2
        
        enemy_id = closest_enemy.get("id", "")
        enemy_hp = float(closest_enemy.get("hp", 100.0))

        # 1. Hitung statistik bertarung musuh
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
            my_combat_stats, enemy_combat_stats, self.game_state.hp, enemy_hp
        )

        # 4. Formulasi Keputusan Berdasarkan Jarak dan Tingkat Kemenangan
        if win_rate >= 0.60:
            recommendation = "FIGHT"
        elif win_rate < 0.40 and distance <= 1:
            # Bot hanya lari kabur jika musuh berada di Jarak Dekat (wilayah tetangga atau wilayah sama)
            recommendation = "FLEE"
        else:
            recommendation = "STANDBY"

        return {
            "recommendation": recommendation,
            "target": closest_enemy,
            "win_rate": win_rate,
            "distance": distance
        }