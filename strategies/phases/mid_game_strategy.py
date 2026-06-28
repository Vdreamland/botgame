# -*- coding: utf-8 -*-
"""
ClawRoyale Mid Game Strategy.
Balances secure ruin exploration with hunting highly vulnerable targets [11].
"""

from typing import Dict, Any, Optional, Tuple
from core.state.game_state import GameState
from strategies.combat.battle_analyzer import BattleAnalyzer
from strategies.exploration.ruin_explorer import RuinExplorer


class MidGameStrategy:
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.battle_analyzer = BattleAnalyzer(game_state)
        self.ruin_explorer = RuinExplorer(game_state)

    def determine_mid_action(self, battle_eval: Dict[str, Any]) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Decides mid-game trade-offs between fighting and exploring [11].
        """
        recommendation = battle_eval.get("recommendation", "STANDBY")
        target = battle_eval.get("target")

        # 1. Prioritas Utama: Jika ada musuh yang sangat lemah (Win Rate Tinggi), paksa duel [11]
        if recommendation == "FIGHT" and target:
            return "HUNT", target

        # 2. Prioritas Kedua: Bersihkan ruins terdekat jika kondisi alert gauge aman [10]
        can_explore, _ = self.ruin_explorer.is_safe_to_explore()
        if can_explore:
            return "EXPLORE", None

        # 3. Default: Standby / Bersiap siaga menjaga posisi
        return "STANDBY", None