# -*- coding: utf-8 -*-
"""
ClawRoyale Shared Team Registry (Thread-Safe & Async-Safe Singleton).
Ensures bot instances can register and detect teammates to avoid friendly fire.
"""

import threading
from typing import Set


class TeamRegistry:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """
        Enforces singleton pattern to ensure all running bots access the exact same
        in-memory teammate database.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TeamRegistry, cls).__new__(cls)
                cls._instance._ally_ids = set()
                cls._instance._ally_names = set()
                cls._instance._data_lock = threading.Lock()
            return cls._instance

    def register_ally(self, player_id: str, name: str) -> None:
        """
        Registers a bot instance as an authorized ally.
        :param player_id: Dynamic in-game player ID assigned by the server.
        :param name: Public name/username of the bot.
        """
        with self._data_lock:
            if player_id:
                self._ally_ids.add(player_id)
            if name:
                self._ally_names.add(name.lower())

    def unregister_ally(self, player_id: str, name: str) -> None:
        """
        Safely removes a bot instance from active teammate registry when game ends.
        """
        with self._data_lock:
            self._ally_ids.discard(player_id)
            self._ally_names.discard(name.lower())

    def is_ally(self, player_id: str, name: str = "") -> bool:
        """
        Checks whether a player ID or name belongs to our teammate bots.
        """
        with self._data_lock:
            if player_id and player_id in self._ally_ids:
                return True
            if name and name.lower() in self._ally_names:
                return True
            return False

    def clear_all(self) -> None:
        """
        Clears the entire registry (primarily for system testing).
        """
        with self._data_lock:
            self._ally_ids.clear()
            self._ally_names.clear()