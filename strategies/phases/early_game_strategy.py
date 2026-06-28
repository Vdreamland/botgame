# -*- coding: utf-8 -*-
"""
ClawRoyale Early Game Strategy.
Focuses on collecting RGB relics to form a 'fullSet' and exploring low-alert ruins [9, 10].
"""

from typing import Dict, Any, Optional, Tuple
from core.state.game_state import GameState
from strategies.scanners.ground_item_scanner import GroundItemScanner
from strategies.exploration.ruin_explorer import RuinExplorer


class EarlyGameStrategy:
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.item_scanner = GroundItemScanner(game_state)
        self.ruin_explorer = RuinExplorer(game_state)

    def determine_early_action(self) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Computes early game priorities.
        Returns: Tuple[action_type, details_dict]
        """
        # 1. Prioritas Utama: Cari & Ambil Item Relic/Weapons berharga di tanah sekitar [9]
        best_item = self.item_scanner.find_highest_utility_item()
        if best_item and best_item.get("utility_score", 0.0) >= 1.0:
            item_id = best_item.get("id") or best_item.get("itemId")
            return "PICKUP", {"item_id": item_id}

        # 2. Prioritas Kedua: Lakukan eksplorasi ruin jika berada di tile Ruins [10]
        can_explore, reason = self.ruin_explorer.is_safe_to_explore()
        if can_explore:
            return "EXPLORE", None

        # 3. Prioritas Ketiga: Cari ruins terdekat jika tidak berdiri di tile Ruins
        return "LOOT_OR_EXPLORE_PASSIVE", None