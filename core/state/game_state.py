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

        self.current_action = "Waiting in Queue"
        self.current_target = "None"

    def update_from_server_frame(self, frame: Dict[str, Any]) -> None:
        """
        Parses incoming game state updates from the WebSocket server [8, 10, 11].
        Supports both REST payload shapes and official /ws/agent WebSocket view structures.
        """
        frame_type = frame.get("type")
        data = frame.get("data", {}) if frame.get("data") else frame

        if frame_type == "error":
            err_msg = frame.get("message", data.get("message", "Unknown server error"))
            self.logger.error(f"SERVER REJECTION: {err_msg}")
            return

        if frame_type == "agent_view":
            # Dapatkan objek view & self_state yang valid dari WebSocket payload resmi [Gameplay WebSocket]
            view = data.get("view", {}) if isinstance(data, dict) else {}
            self_state = view.get("self") or data.get("self") or data.get("agent") or {}
            
            if self_state:
                # Daftarkan Player ID yang digunakan untuk pemfilteran aksi
                resolved_id = self_state.get("id") or frame.get("agentId")
                if not self.player_id and resolved_id:
                    self.player_id = resolved_id
                    self.team_registry.register_ally(self.player_id, self.agent_name)
                    self.logger.info(f"Registered Player ID: {self.player_id} into the Team Registry.")

                self.hp = float(self_state.get("hp", self.hp))
                self.ep = float(self_state.get("ep", self.ep))
                self.q = int(self_state.get("q", self.q))
                self.r = int(self_state.get("r", self.r))
                
                # alertGauge ada di dalam self_state berdasarkan dokumentasi resmi
                self.alert_gauge = int(self_state.get("alertGauge", self.alert_gauge))

                loadout = self_state.get("loadout", {})
                self.equipped_weapon = loadout.get("weapon") or self_state.get("equippedWeapon", "")
                self.equipped_armor = loadout.get("armor", "")
                self.equipped_relics = loadout.get("relics", [])
                self.has_full_set = loadout.get("fullSet", False)

            # Ekstrak data wilayah / mapContext
            current_region = view.get("currentRegion", {})
            map_context = data.get("mapContext", {}) or {}
            
            # Gabungkan parsing data wilayah dari dokumentasi resmi / legacy
            self.current_terrain = current_region.get("terrain") or map_context.get("terrain") or self.current_terrain
            self.current_weather = current_region.get("weather") or map_context.get("weather") or self.current_weather
            self.is_death_zone = bool(current_region.get("isDeathZone", map_context.get("isDeathZone", self.is_death_zone)))
            
            # Turn bisa berada di tingkat atas frame atau di mapContext
            self.turn = int(frame.get("turn") or data.get("turn") or map_context.get("turn") or self.turn)
            self.day = int(map_context.get("day") or self.day)

            # Ground items berada di view.currentRegion.items atau data.items
            self.items_on_ground = current_region.get("items") or data.get("items") or []

            # Musuh & Aliansi berada di view.visibleAgents atau data.players
            other_players = view.get("visibleAgents") or data.get("players") or []
            clean_enemies = []
            clean_allies = []

            for p in other_players:
                p_id = p.get("id") or p.get("agentId") or ""
                p_name = p.get("name") or p.get("agentName") or ""

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

        elif frame_type == "hp_changed":
            # Ekstrak ID target secara berlapis (termasuk objek bersarang)
            agent_obj = data.get("agent", {}) if isinstance(data, dict) else {}
            player_obj = data.get("player", {}) if isinstance(data, dict) else {}
            frame_agent = frame.get("agent", {}) if isinstance(frame, dict) else {}
            frame_player = frame.get("player", {}) if isinstance(frame, dict) else {}

            target_player_id = (
                agent_obj.get("id") or player_obj.get("id") or
                frame_agent.get("id") or frame_player.get("id") or
                data.get("agentId") or data.get("playerId") or data.get("id") or
                frame.get("agentId") or frame.get("playerId") or frame.get("id") or ""
            )

            if target_player_id == self.player_id:
                new_hp = float(
                    data.get("hp") or frame.get("hp") or
                    agent_obj.get("hp") or frame_agent.get("hp") or
                    self.hp
                )
                self.hp = new_hp
                self.logger.info(f"Health update received: {self.hp:.1f}%")

        elif frame_type == "agent_moved":
            # Ekstrak ID pelaku gerak secara berlapis (termasuk objek bersarang)
            agent_obj = data.get("agent", {}) if isinstance(data, dict) else {}
            player_obj = data.get("player", {}) if isinstance(data, dict) else {}
            frame_agent = frame.get("agent", {}) if isinstance(frame, dict) else {}
            frame_player = frame.get("player", {}) if isinstance(frame, dict) else {}

            moving_player_id = (
                agent_obj.get("id") or player_obj.get("id") or
                frame_agent.get("id") or frame_player.get("id") or
                data.get("agentId") or data.get("playerId") or data.get("id") or
                frame.get("agentId") or frame.get("playerId") or frame.get("id") or ""
            )

            if moving_player_id == self.player_id:
                new_q = int(
                    data.get("q") or frame.get("q") or
                    agent_obj.get("q") or frame_agent.get("q") or
                    self.q
                )
                new_r = int(
                    data.get("r") or frame.get("r") or
                    agent_obj.get("r") or frame_agent.get("r") or
                    self.r
                )
                self.q = new_q
                self.r = new_r
                self.logger.info(f"Coordinates synchronized: Moved to hex ({self.q}, {self.r}) [8].")

    def clean_session_data(self) -> None:
        if self.player_id:
            self.team_registry.unregister_ally(self.player_id, self.agent_name)
            
        self.player_id = ""
        self.items_on_ground.clear()
        self.enemies.clear()
        self.allies_nearby.clear()
        self.current_action = "Waiting in Queue"
        self.current_target = "None"
        self.logger.info("Local GameState session successfully cleared.")