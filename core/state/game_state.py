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

        # Data Vital Agen Saat Ini
        self.player_id: str = ""
        self.hp: float = 100.0
        self.ep: float = 30.0
        
        # Posisi Koordinat Heksagonal (Axial: q, r) [8]
        self.q: int = 0
        self.r: int = 0

        # Status Lingkungan Arena [10]
        self.alert_gauge: int = 0
        self.current_terrain: str = "chapel"
        self.current_weather: str = "sunny"
        self.is_death_zone: bool = False
        self.day: int = 1
        self.turn: int = 1

        # Perlengkapan Aktif & Status Sinergi [9]
        self.equipped_weapon: str = ""
        self.equipped_armor: str = ""
        self.equipped_relics: List[str] = []
        self.has_full_set: bool = False

        # Entitas Terdeteksi di Jangkauan Visual
        self.items_on_ground: List[Dict[str, Any]] = []
        self.enemies: List[Dict[str, Any]] = []  # Hanya berisi musuh asli, sekutu difilter keluar
        self.allies_nearby: List[Dict[str, Any]] = []  # Informasi sekutu kita di sekitar koordinat

    def update_from_server_frame(self, frame: Dict[str, Any]) -> None:
        """
        Parses incoming game state updates from the WebSocket server.
        Synchronizes HP, EP, coordinates, ground items, weather, and filters teammates.
        """
        frame_type = frame.get("type")
        
        # Hanya tangani tipe frame sinkronisasi state
        if frame_type not in ["state", "game_state", "tick", "action_result"]:
            return

        data = frame.get("data", {})
        if not data:
            return

        # 1. Sinkronisasi Data Vital & Posisi Agent Kita
        self_state = data.get("self", {})
        if self_state:
            # Player ID penetapan server
            if not self.player_id and self_state.get("id"):
                self.player_id = self_state.get("id")
                # Daftarkan diri ke tim registry global agar bot lain tahu kita adalah kawan
                self.team_registry.register_ally(self.player_id, self.agent_name)
                self.logger.info(f"Registered Player ID: {self.player_id} into the Team Registry.")

            self.hp = float(self_state.get("hp", self.hp))
            self.ep = float(self_state.get("ep", self.ep))
            
            # Update Koordinat Axial [8]
            self.q = int(self_state.get("q", self.q))
            self.r = int(self_state.get("r", self.r))

            # Update Perlengkapan Terpasang [9]
            loadout = self_state.get("loadout", {})
            self.equipped_weapon = loadout.get("weapon", "")
            self.equipped_armor = loadout.get("armor", "")
            self.equipped_relics = loadout.get("relics", [])
            self.has_full_set = loadout.get("fullSet", False)

        # 2. Sinkronisasi Informasi Lingkungan Peta Heksagonal [10]
        map_context = data.get("mapContext", {})
        if map_context:
            self.alert_gauge = int(map_context.get("alertGauge", self.alert_gauge))
            self.current_terrain = map_context.get("terrain", self.current_terrain)
            self.current_weather = map_context.get("weather", self.current_weather)
            self.is_death_zone = bool(map_context.get("isDeathZone", self.is_death_zone))
            self.day = int(map_context.get("day", self.day))
            self.turn = int(map_context.get("turn", self.turn))

        # 3. Sinkronisasi Item di Tanah (Ground Items)
        self.items_on_ground = data.get("items", [])

        # 4. Sinkronisasi & Penyaringan Pemain Lain (Enemies vs Allies)
        other_players = data.get("players", [])
        clean_enemies = []
        clean_allies = []

        for p in other_players:
            p_id = p.get("id", "")
            p_name = p.get("name", "")

            # Lewati diri sendiri jika terkirim oleh server
            if p_id == self.player_id:
                continue

            # Gunakan TeamRegistry untuk memisahkan Teman dan Musuh
            if self.team_registry.is_ally(p_id, p_name):
                clean_allies.append(p)
            else:
                clean_enemies.append(p)

        self.enemies = clean_enemies
        self.allies_nearby = clean_allies
        
        # Cetak log ringkasan jika mendeteksi ancaman
        if len(self.enemies) > 0:
            self.logger.warning(
                f"Sync completed: Detected {len(self.enemies)} actual enemies "
                f"and {len(self.allies_nearby)} ally bots nearby."
            )

    def clean_session_data(self) -> None:
        """
        Cleans dynamic state info when leaving active gameplay matches.
        """
        # Hapus diri dari registry tim sebelum logout jika ID valid
        if self.player_id:
            self.team_registry.unregister_ally(self.player_id, self.agent_name)
            
        self.player_id = ""
        self.items_on_ground.clear()
        self.enemies.clear()
        self.allies_nearby.clear()
        self.logger.info("Local GameState session successfully cleared.")