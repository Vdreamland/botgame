# -*- coding: utf-8 -*-
"""
ClawRoyale Cooldown Manager.
Tracks action availability locally to prevent server rejection (canAct=False) [12].
"""

import time


class CooldownManager:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self._can_act_server = True
        self._cooldown_end_time = 0.0

    def set_action_cooldown(self, duration: float = 30.0) -> None:
        """
        Locks actions locally by setting an absolute timestamp limit.
        Used immediately after transmitting a cooldown action [12].
        """
        self._cooldown_end_time = time.monotonic() + duration

    def update_server_can_act(self, server_can_act: bool) -> None:
        """
        Updates action availability status based on incoming state results from the WS server.
        """
        self._can_act_server = server_can_act

    def get_remaining_cooldown(self) -> float:
        """
        Returns the remaining lock duration in seconds.
        """
        now = time.monotonic()
        remaining = self._cooldown_end_time - now
        return max(0.0, remaining)

    def can_execute_action(self) -> bool:
        """
        Validates action readiness.
        Returns True only if both server and local timers permit.
        """
        # Cek sisa cooldown lokal
        if self.get_remaining_cooldown() > 0.0:
            return False
            
        # Cek bendera canAct dari server
        return self._can_act_server