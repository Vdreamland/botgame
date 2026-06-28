# -*- coding: utf-8 -*-
"""
ClawRoyale Combat Victory Simulator.
Simulates turn-by-turn battles using official damage formulas [11].
"""

import math
from typing import Dict, Any


class VictoryCalculator:
    @staticmethod
    def simulate_battle_outcome(my_stats: Dict[str, Any], enemy_stats: Dict[str, Any], 
                                my_current_hp: float, enemy_current_hp: float) -> float:
        """
        Simulates turn-by-turn trade of attacks until one party's HP drops to 0.
        Damage Formula: (ATK + weapon_bonus) - (target_DEF * 0.5) (Min 1 damage) [11].
        Returns: Winning probability score (0.0 to 1.0).
        """
        # 1. Ambil data efektivitas statistik bertarung [11]
        my_atk = float(my_stats.get("effective_atk", 10.0))
        my_def = float(my_stats.get("effective_def", 5.0))
        
        enemy_atk = float(enemy_stats.get("effective_atk", 10.0))
        enemy_def = float(enemy_stats.get("effective_def", 5.0))

        # 2. Hitung Nilai Damage Bersih per Turn (Minimal 1) [11]
        damage_to_enemy = max(1.0, my_atk - (enemy_def * 0.5))
        damage_to_me = max(1.0, enemy_atk - (my_def * 0.5))

        # 3. Hitung Jumlah Turn yang Dibutuhkan untuk Mengeliminasi Lawan
        turns_to_kill_enemy = math.ceil(enemy_current_hp / damage_to_enemy)
        turns_to_kill_me = math.ceil(my_current_hp / damage_to_me)

        # 4. Evaluasi Hasil Simulasi
        if turns_to_kill_enemy < turns_to_kill_me:
            # Bot menang lebih cepat. Hitung margin kesehatan sisa
            surviving_hp = my_current_hp - ((turns_to_kill_enemy - 1) * damage_to_me)
            # Menghasilkan skor utilitas kemenangan tinggi (0.75 - 1.0)
            win_rate = 0.75 + (0.25 * (surviving_hp / my_current_hp))
            return min(1.0, win_rate)
            
        elif turns_to_kill_enemy == turns_to_kill_me:
            # Seri (Saling mengeliminasi di turn yang sama). Bot dinilai memiliki peluang 50%
            return 0.50
            
        else:
            # Bot kalah lebih cepat. Hitung seberapa jauh kegagalannya
            failed_ratio = turns_to_kill_me / turns_to_kill_enemy
            # Menghasilkan skor utilitas kemenangan rendah (0.0 - 0.45)
            win_rate = 0.45 * failed_ratio
            return max(0.0, win_rate)