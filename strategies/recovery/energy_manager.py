# -*- coding: utf-8 -*-
"""
ClawRoyale Energy Point (EP) Manager.
Decides when to Rest safely to replenish EP without risking exposure to danger [12, 14].
"""

from core.state.game_state import GameState
from config.settings import AI_SETTINGS


class EnergyManager:
    def __init__(self, game_state: GameState):
        self.game_state = game_state

    def should_execute_rest(self, enemies_nearby_count: int) -> bool:
        """
        Evaluates current EP and environmental threats to verify if Resting is safe [12, 14].
        :param enemies_nearby_count: Count of hostile players in immediate vicinity.
        :return: True if Rest action is recommended, else False.
        """
        current_ep = self.game_state.ep

        # Kondisi 1: EP bot sudah penuh atau masih dalam batas aman optimal
        if current_ep >= AI_SETTINGS["ep_optimal_reserve"]:
            return False

        # Kondisi 2: Bahaya ekstrem - Ada musuh di dekat kita. Jangan pernah diam (rest) [12]
        if enemies_nearby_count > 0:
            return False

        # Kondisi 3: Bahaya ekstrim - Bot berada di dalam wilayah Dead Zone. Harus terus bergerak lari [14]
        if self.game_state.is_death_zone:
            return False

        # Kondisi 4: Bahaya alert gauge lokal menyentuh batas panik (Jangan rest jika guardian akan spawn)
        if self.game_state.alert_gauge >= AI_SETTINGS["alert_gauge_panic"]:
            return False

        # Skenario A: EP berada di bawah batas kritis mutlak (EP < 5) -> Wajib paksa Rest [12]
        if current_ep < AI_SETTINGS["ep_minimum_reserve"]:
            return True

        # Skenario B: Bot berada di area aman dan EP di bawah batas optimal -> Lakukan Rest untuk investasi turn selanjutnya
        if current_ep < AI_SETTINGS["ep_optimal_reserve"]:
            return True

        return False