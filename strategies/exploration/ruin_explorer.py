# -*- coding: utf-8 -*-
"""
ClawRoyale Ruin Exploration Strategy.
Coordinates exploration limits by tracking the alert gauge to avoid spawning Guardians [10].
"""

from typing import Dict, Any, Tuple
from config.settings import AI_SETTINGS
from config.game_constants import ALERT_DECAY_PER_TURN, ALERT_EXPLORE_PENALTY, ALERT_GAUGE_MAX
from core.state.game_state import GameState


class RuinExplorer:
    def __init__(self, game_state: GameState):
        self.game_state = game_state

    def is_safe_to_explore(self) -> Tuple[bool, str]:
        """
        Checks if the agent can safely execute an explore action on the current tile [10, 12].
        :return: Tuple of (is_safe_bool, reason_string)
        """
        # Kondisi 1: Pastikan bot berdiri tepat di tile ruins atau s-relic [10]
        current_terrain = self.game_state.current_terrain.lower()
        if "ruin" not in current_terrain and "relic" not in current_terrain:
            return False, f"Not standing on an explorable ruins tile. Current: {current_terrain}"

        # Kondisi 2: Cek ketersediaan energi dasar (Explore memakan 1 EP) [10]
        if self.game_state.ep < 1.0:
            return False, "Insufficient EP to execute exploration."

        # Kondisi 3: Cek status Alert Gauge [10]
        current_alert = self.game_state.alert_gauge
        
        # Perkirakan sisa alert jika melakukan explore turn ini (+2 poin) [10]
        estimated_alert_after_explore = current_alert + ALERT_EXPLORE_PENALTY

        # Jangan lakukan explore jika nilai gauge setelah aksi menyentuh atau melewati batas bahaya
        if estimated_alert_after_explore >= AI_SETTINGS["alert_gauge_panic"]:
            return False, (
                f"Alert gauge warning! Current: {current_alert}/10. "
                f"Exploring now will push gauge to {estimated_alert_after_explore}, risking Guardian spawns [10]."
            )

        return True, "Safe to explore ruins."

    def estimate_turns_to_wait_for_decay(self) -> int:
        """
        Calculates how many turns the agent needs to wait (e.g. resting or moving)
        to decay the alert gauge back to safe levels [10].
        """
        current_alert = self.game_state.alert_gauge
        safe_level = AI_SETTINGS["alert_gauge_safe"]

        if current_alert <= safe_level:
            return 0

        excess_alert = current_alert - safe_level
        
        # Alert luruh sebanyak 4 poin per turn [10]
        decay_rate = abs(ALERT_DECAY_PER_TURN)
        
        import math
        return math.ceil(excess_alert / decay_rate)