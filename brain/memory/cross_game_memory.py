# -*- coding: utf-8 -*-
"""
ClawRoyale Cross-Game Memory Manager.
Handles persistent storage of tactical game history and learning logs.
"""

import os
import json
from typing import Dict, Any

MEMORY_DIR = "brain/memory"
os.makedirs(MEMORY_DIR, exist_ok=True)


class CrossGameMemory:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.safe_name = agent_name.lower().replace(" ", "_")
        self.memory_file = os.path.join(MEMORY_DIR, f"{self.safe_name}_context.json")
        self.data: Dict[str, Any] = self._load_memory()

    def _load_memory(self) -> Dict[str, Any]:
        """Loads historical context from disk."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return self._get_default_schema()
        return self._get_default_schema()

    def _get_default_schema(self) -> Dict[str, Any]:
        return {
            "total_games": 0,
            "total_wins": 0,
            "total_losses": 0,
            "frequent_safe_zones": [],
            "encountered_enemies": {},
            "last_active_day": 1
        }

    def save_memory(self) -> None:
        """Saves current state to local JSON file securely."""
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def record_match_result(self, is_win: bool) -> None:
        """
        Updates victory and defeat statistics for analytical auditing.
        """
        self.data["total_games"] += 1
        if is_win:
            self.data["total_wins"] += 1
        else:
            self.data["total_losses"] += 1
        self.save_memory()

    def log_enemy_encounter(self, enemy_name: str, used_weapon: str) -> None:
        """
        Keeps track of encountered players and their known weapon preferences [11].
        """
        enemies = self.data.setdefault("encountered_enemies", {})
        low_name = enemy_name.lower()
        
        entry = enemies.setdefault(low_name, {"encounters": 0, "known_weapons": []})
        entry["encounters"] += 1
        if used_weapon and used_weapon not in entry["known_weapons"]:
            entry["known_weapons"].append(used_weapon)
            
        self.save_memory()