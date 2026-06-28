# -*- coding: utf-8 -*-
"""
ClawRoyale Game State Parser and Synchronization Sync.
Maintains coordinates, health, energy, map context, item positions, and filters allies [8, 10].
"""

from typing import Dict, Any, List, Tuple
from utils.logger import AgentLogger
from core.state.team_registry import TeamRegistry


class GameState:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = AgentLogger.get_logger(agent_name)
        self.team_registry = TeamRegistry()

        self.player_id: str = ""
        self.hp: float = 100.0
        self.ep: float = 10.0
        
        self.q: int = 0
        self.r: int = 0

        self.alert_gauge: int = 0
        self.current_terrain: str = "plains"
        self.current_weather: str = "clear"
        self.is_death_zone: bool = False
        self.day: int = 1
        self.turn: int = 1

        self.equipped_weapon: str = ""
        self.equipped_armor: str = ""
        self.equipped_relics: List[str] = []
        self.has_full_set: bool = False

        self.items_on_ground: List[Dict[str, Any]] = []
        self.enemies: List[Dict[str, Any]] = []
        self.allies_nearby: List[Dict[str, Any]] = []

        self.current_action: str = "Waiting in Queue"
        self.current_target: str = "None"

    def update_from_server_frame(self, frame: Dict[str, Any]) -> None:
        """
        Parses incoming game state updates from the WebSocket server.
        Synchronizes HP, EP, coordinates, ground items, weather, and filters teammates [8, 10, 11].
        """
        frame_type = frame.get("type")
        data = frame.get("data", {}) if frame.get("data") else frame

        if frame_type == "agent_view":
            self_state = data.get("self", data.get("agent", {}))
            if self_state:
                if not self.player_id and self_state.get("id"):
                    self.player_id = self_state.get("id")
                    self.team_registry.register_ally(self.player_id, self.agent_name)
                    self.logger.info(f"Registered Player ID: {self.player_id} into the Team Registry.")

                self.hp = float(self_state.get("hp", self.hp))
                self.ep = float(self_state.get("ep", self.ep))
                
                self.q = int(self_state.get("q", self.q))
                self.r = int(self_state.get("r", self.r))

                loadout = self_state.get("loadout", {})
                self.equipped_weapon = loadout.get("weapon", "")
                self.equipped_armor = loadout.get("armor", "")
                self.equipped_relics = loadout.get("relics", [])
                self.has_full_set = loadout.get("fullSet", False)

            map_context = data.get("mapContext", {})
            if map_context:
                self.alert_gauge = int(map_context.get("alertGauge", self.alert_gauge))
                self.current_terrain = map_context.get("terrain", self.current_terrain)
                self.current_weather = map_context.get("weather", self.current_weather)
                self.is_death_zone = bool(map_context.get("isDeathZone", self.is_death_zone))
                self.day = int(map_context.get("day", self.day))
                self.turn = int(map_context.get("turn", self.turn))

            self.items_on_ground = data.get("items", [])

            other_players = data.get("players", [])
            clean_enemies = []
            clean_allies = []

            for p in other_players:
                p_id = p.get("id", "")
                p_name = p.get("name", "")

                if p_id == self.player_id:
                    continue

                if self.team_registry.is_ally(p_id, p_name):
                    clean_allies.append(p)
                else:
                    clean_enemies.append(p)

            self.enemies = clean_enemies
            self.allies_nearby = clean_allies
            
            if len(self.enemies) > 0:
                self.logger.warning(
                    f"Sync completed: Detected {len(self.enemies)} actual enemies "
                    f"and {len(self.allies_nearby)} ally bots nearby."
                )

        elif frame_type == "turn_advanced":
            new_day = int(data.get("day", self.day))
            new_turn = int(data.get("turn", self.turn))
            
            self.logger.info(f"=== NEW GAME TURN: DAY {new_day} | TURN {new_turn} ===")
            
            self.day = new_day
            self.turn = new_turn
            self.current_weather = data.get("weather", self.current_weather)

        # Hanya urai dan catat perubahan darah jika ID cocok dengan bot kita sendiri
        elif frame_type == "hp_changed":
            target_player_id = data.get("id", data.get("playerId", frame.get("id", "")))
            if not target_player_id or target_player_id == self.player_id:
                new_hp = float(data.get("hp", frame.get("hp", self.hp)))
                self.hp = new_hp
                self.logger.info(f"Health update received: {self.hp:.1f}%")

        # Hanya urai dan catat perpindahan koordinat jika ID cocok dengan bot kita sendiri [8]
        elif frame_type == "agent_moved":
            moving_player_id = data.get("id", data.get("playerId", frame.get("id", "")))
            if not moving_player_id or moving_player_id == self.player_id:
                new_q = int(data.get("q", frame.get("q", self.q)))
                new_r = int(data.get("r", frame.get("r", self.r)))
                self.q = new_q
                self.r = new_r
                self.logger.info(f"Coordinates synchronized: Moved to hex ({self.q}, {self.r}) [8].")

    def clean_session_data(self) -> None:
        """
        Cleans dynamic state info when leaving active gameplay matches.
        """
        if self.player_id:
            self.team_registry.unregister_ally(self.player_id, self.agent_name)
            
        self.player_id = ""
        self.items_on_ground.clear()
        self.enemies.clear()
        self.allies_nearby.clear()
        self.current_action = "Waiting in Queue"
        self.current_target = "None"
        self.logger.info("Local GameState session successfully cleared.")