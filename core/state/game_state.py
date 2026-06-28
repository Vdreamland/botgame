# -*- coding: utf-8 -*-
"""
ClawRoyale Game State Parser and Synchronization Sync.
Maintains region context, health, energy, map connections, and filters allies [8, 10].
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
        
        # Dipertahankan bernilai 0 hanya untuk kompatibilitas impor modul lain agar tidak memicu AttributeError
        self.q: int = 0
        self.r: int = 0

        self.current_region_id: str = "region_0_0"
        self.current_region_name: str = "Plains"
        self.connections: List[str] = []
        self.visible_ruins: List[Dict[str, Any]] = []
        self.visible_monsters: List[Dict[str, Any]] = []

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

        # Parsing penuh dilakukan untuk 'agent_view' (awal game) dan 'turn_advanced' (setiap ganti turn)
        if frame_type in ["agent_view", "turn_advanced"]:
            if frame_type == "turn_advanced":
                new_day = int(data.get("day") or data.get("view", {}).get("currentRegion", {}).get("day") or self.day)
                new_turn = int(data.get("turn") or data.get("view", {}).get("currentRegion", {}).get("turn") or self.turn)
                self.logger.info(f"=== NEW GAME TURN: DAY {new_day} | TURN {new_turn} ===")
                self.day = new_day
                self.turn = new_turn

            view = data.get("view", {}) if isinstance(data, dict) else {}
            self_state = view.get("self") or data.get("self") or data.get("agent") or {}
            
            if self_state:
                resolved_id = self_state.get("id") or frame.get("agentId")
                if not self.player_id and resolved_id:
                    self.player_id = resolved_id
                    self.team_registry.register_ally(self.player_id, self.agent_name)
                    self.logger.info(f"Registered Player ID: {self.player_id} into the Team Registry.")

                self.hp = float(self_state.get("hp", self.hp))
                self.ep = float(self_state.get("ep", self.ep))
                self.alert_gauge = int(self_state.get("alertGauge", self.alert_gauge))

                loadout = self_state.get("loadout", {})
                self.equipped_weapon = loadout.get("weapon") or self_state.get("equippedWeapon", "")
                self.equipped_armor = loadout.get("armor", "")
                self.equipped_relics = loadout.get("relics", [])
                self.has_full_set = loadout.get("fullSet", False)

            # Ekstrak data wilayah / mapContext
            current_region = view.get("currentRegion", {})
            map_context = data.get("mapContext", {}) or {}
            
            old_region_id = self.current_region_id
            self.current_region_id = current_region.get("id") or data.get("currentRegionId") or self.current_region_id
            self.current_region_name = current_region.get("name") or data.get("currentRegionName") or self.current_region_name
            self.connections = current_region.get("connections") or data.get("connections") or []
            self.visible_ruins = view.get("visibleRuins") or data.get("visibleRuins") or []
            self.visible_monsters = view.get("visibleMonsters") or data.get("visibleMonsters") or []

            # Cetak log sinkronisasi jika bot sukses berpindah wilayah
            if old_region_id != self.current_region_id and self.player_id:
                self.logger.info(f"Coordinates synchronized: Moved to region {self.current_region_name} ({self.current_region_id}) [8].")

            # Resolusi terrain dari nama region jika key 'terrain' absen
            region_name = self.current_region_name.lower()
            resolved_terrain = ""
            if "forest" in region_name or "wood" in region_name:
                resolved_terrain = "forest"
            elif "ruin" in region_name or "temple" in region_name or "relic" in region_name:
                resolved_terrain = "ruins"
            elif "hill" in region_name or "mountain" in region_name or "ridge" in region_name:
                resolved_terrain = "hills"
            elif "water" in region_name or "lake" in region_name or "river" in region_name or "sea" in region_name or "swamp" in region_name:
                resolved_terrain = "water"
            else:
                resolved_terrain = "plains"

            self.current_terrain = (
                current_region.get("terrain") or 
                map_context.get("terrain") or 
                resolved_terrain
            ).lower()
            
            self.current_weather = current_region.get("weather") or map_context.get("weather") or self.current_weather
            self.is_death_zone = bool(current_region.get("isDeathZone", map_context.get("isDeathZone", self.is_death_zone)))
            
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

                # PENGAMAN MUTLAK: Lewati dan abaikan musuh yang sudah mati (isAlive == False atau HP <= 0)
                p_is_alive = p.get("isAlive")
                p_hp = p.get("hp")
                if p_is_alive is False or (p_hp is not None and float(p_hp) <= 0.0):
                    continue

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
                old_region_id = self.current_region_id
                self.current_region_id = data.get("regionId") or frame.get("regionId") or self.current_region_id
                self.current_region_name = data.get("regionName") or frame.get("regionName") or self.current_region_name
                
                if old_region_id != self.current_region_id:
                    self.logger.info(f"Coordinates synchronized: Moved to region {self.current_region_name} ({self.current_region_id}) [8].")

    def clean_session_data(self) -> None:
        if self.player_id:
            self.team_registry.unregister_ally(self.player_id, self.agent_name)
            
        self.player_id = ""
        self.items_on_ground.clear()
        self.enemies.clear()
        self.allies_nearby.clear()
        self.visible_monsters.clear()
        self.current_action = "Waiting in Queue"
        self.current_target = "None"
        self.connections.clear()
        self.visible_ruins.clear()
        self.logger.info("Local GameState session successfully cleared.")