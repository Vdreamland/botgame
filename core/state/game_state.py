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
        
        # Memori dinamis untuk menghafal nama wilayah baru dari server secara real-time
        self.dynamic_region_names: Dict[str, str] = {}

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

        self.inventory: List[Dict[str, Any]] = []
        self.items_on_ground: List[Dict[str, Any]] = []
        self.enemies: List[Dict[str, Any]] = []
        self.allies_nearby: List[Dict[str, Any]] = []

        self.current_action = "Waiting in Queue"
        self.current_target = "None"

    def get_region_name(self, region_id: str) -> str:
        """
        Translates a raw region UUID into its human-readable region name.
        Uses both static log-based registry and real-time dynamic caching.
        """
        if not region_id:
            return "Unknown"
        
        if region_id in self.dynamic_region_names:
            return self.dynamic_region_names[region_id]
            
        # Kamus database pemetaan UUID wilayah sah berdasarkan log lobi Anda
        STATIC_REGION_MAP = {
            "268745f0-d5a9-4868-bdcb-89267143c99b": "Alley",
            "0f0e0bcb-2d48-4930-9b8e-a585b3d3d7f7": "Downtown",
            "078a7687-005a-44d3-b86d-376090710630": "Lake",
            "5ee70777-714b-4595-9021-803f226fa779": "Reactor",
            "d05ec9cf-eff7-410b-b938-23937079f93d": "Lab",
            "7661219c-8512-42e8-a228-aac2a2fbc075": "Lab",
            "43dae327-69fc-44ff-80b2-3a66fcbfb0a3": "S:Relic",
            "5a53e0a9-81b9-4fd2-bcb3-2ffc9bdb336a": "S:Relic",
            "8ebdb6ab-68bc-45f5-9401-03870f05f0e5": "S:Relic",
            "a86c6662-fc40-4801-bfda-40559aa0987c": "Suburbs",
            "6c82c33e-abe3-4491-a048-777bcf2c13da": "Airport",
            "5803a56c-32ba-4286-9221-8b57ff230a62": "Vault",
            "7405bf87-4a59-4d6c-881b-cfaf1ee6395c": "Camp",
            "a16235ed-b5d5-4031-97eb-2790934feb07": "Hospital",
            "f23cf0df-cb9d-4f2d-9e6e-3dd245160cf1": "Shrine",
            "30f42196-b933-4bf3-9362-e365c9a5686a": "Cliff",
            "401eb1a7-4ed4-46b1-9d0b-e20459ac3aff": "Crossroads"
        }
        
        if region_id in STATIC_REGION_MAP:
            return STATIC_REGION_MAP[region_id]
            
        return f"Region {region_id[:8]}"

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
                
                # Sinkronisasikan daftar isi tas inventaris bot agar EquipSelector dapat mendeteksinya
                self.inventory = self_state.get("inventory", [])

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

            # Daftarkan secara dinamis ubin yang sedang kita injak saat ini ke memori
            if self.current_region_id and self.current_region_name:
                self.dynamic_region_names[self.current_region_id] = self.current_region_name

            # Daftarkan wilayah Dead Zone yang akan meluas secara dinamis dari server
            pending_zones = view.get("pendingDeathzones") or data.get("pendingDeathzones") or []
            for zone in pending_zones:
                z_id = zone.get("id")
                z_name = zone.get("name")
                if z_id and z_name:
                    self.dynamic_region_names[z_id] = z_name

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
            
            # PENINGKATAN LOG (Transparansi Layer Graf): Terjemahkan UUID wilayah ke nama manusiawi
            if len(self.enemies) > 0:
                layer_0 = []
                layer_1 = []
                layer_2 = []
                
                for e in self.enemies:
                    e_region = e.get("regionId") or self.current_region_id
                    e_name = e.get("name", "Unknown")
                    resolved_name = self.get_region_name(e_region)
                    
                    if e_region == self.current_region_id:
                        layer_0.append(f"'{e_name}'")
                    elif e_region in self.connections:
                        layer_1.append(f"'{e_name}' in {resolved_name}")
                    else:
                        layer_2.append(f"'{e_name}' (Safe)")

                self.logger.warning(
                    f"Sync completed: Detected {len(self.enemies)} active enemies. "
                    f"Layer 0 (Same Region): [{', '.join(layer_0)}]. "
                    f"Layer 1 (Adjacent Region): [{', '.join(layer_1)}]. "
                    f"Layer 2+ (Distant Region): {len(layer_2)} enemies."
                )

            # PENINGKATAN LOG (Transparansi Loot): Cetak payload mentah jika item bertipe Unknown
            if self.items_on_ground:
                item_details = []
                for i in self.items_on_ground:
                    i_type = i.get("type") or i.get("name") or i.get("itemType") or "Unknown"
                    i_id = i.get("id") or i.get("itemId") or "Unknown"
                    if i_type == "Unknown":
                        item_details.append(f"Unknown (Raw Data: {i})")
                    else:
                        item_details.append(f"{i_type} (ID: {i_id})")
                self.logger.info(f"Loot radar: Detected {len(self.items_on_ground)} items on ground: {', '.join(item_details)}.")

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