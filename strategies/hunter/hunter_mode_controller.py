# -*- coding: utf-8 -*-
"""
ClawRoyale Hunter Mode Controller.
Manages target locking and evaluates safety boundaries for active hunts [14].
"""

from typing import Dict, Any, Optional
from config.settings import AI_SETTINGS
from core.state.game_state import GameState


class HunterModeController:
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.locked_target_id: Optional[str] = None
        self.locked_target_name: Optional[str] = None

    def should_initiate_hunt(self, battle_evaluation: Dict[str, Any]) -> bool:
        """
        Evaluates whether the agent is healthy enough to lock onto a target.
        Requires high win rate and secure HP/EP reserves before starting a hunt.
        """
        recommendation = battle_evaluation.get("recommendation", "STANDBY")
        win_rate = battle_evaluation.get("win_rate", 0.0)
        target = battle_evaluation.get("target")

        if not target or recommendation != "FIGHT":
            return False

        # Syarat 1: Sisa HP bot harus di atas batas aman (HP > 50%)
        hp_percentage = self.game_state.hp / 100.0
        if hp_percentage < 0.50:
            return False

        # Syarat 2: EP bot harus mencukupi untuk melakukan pengejaran taktis
        if self.game_state.ep < AI_SETTINGS["ep_minimum_reserve"]:
            return False

        # Syarat 3: Peluang menang di atas batas aman yang telah dikalkulasi
        if win_rate < AI_SETTINGS["min_win_rate_for_aggression"]:
            return False

        return True

    def lock_target(self, target_data: Dict[str, Any]) -> None:
        """Locks onto a hostile player."""
        self.locked_target_id = target_data.get("id")
        self.locked_target_name = target_data.get("name")

    def release_target(self) -> None:
        """Clears active target locks."""
        self.locked_target_id = None
        self.locked_target_name = None

    def verify_hunt_safety(self, battle_evaluation: Dict[str, Any]) -> bool:
        """
        Continually verifies if the active hunt is still safe to pursue.
        Breaks target lock if:
        - Bot's HP drops below the panic threshold [35%].
        - Target flees into the Dead Zone [14].
        - Target distance becomes unreachably far.
        """
        if not self.locked_target_id:
            return False

        # Kondisi 1: Cek apakah HP bot menyentuh batas kritis (panic)
        hp_percentage = self.game_state.hp / 100.0
        if hp_percentage < AI_SETTINGS["hp_panic_threshold"]:
            self.release_target()
            return False

        target = battle_evaluation.get("target")
        if not target:
            # Target telah hilang dari jangkauan visual bot
            self.release_target()
            return False

        # Kondisi 2: Pastikan target tidak kabur ke dalam area gas maut Dead Zone [14]
        is_target_in_deathzone = bool(target.get("isDeathZone", False))
        if is_target_in_deathzone:
            # Jangan ikuti musuh ke area Dead Zone karena berbahaya (1.34 HP/s damage) [14]
            self.release_target()
            return False

        # Kondisi 3: Cek apakah target terlampau jauh dari jangkauan scan radius
        distance = battle_evaluation.get("distance", 999)
        if distance > AI_SETTINGS["scan_radius_enemies"]:
            self.release_target()
            return False

        return True