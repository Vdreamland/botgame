# -*- coding: utf-8 -*-
"""
ClawRoyale Autonomous Decision Engine.
The primary orchestrator that processes scanners, hazards, phases, and dispatches actions [11, 12].
"""

import random
import asyncio
from typing import Dict, Any, Optional, Set, Tuple
from utils.logger import AgentLogger

from core.state.game_state import GameState
from actions.action_dispatcher import ActionDispatcher

from strategies.combat.battle_analyzer import BattleAnalyzer
from strategies.combat.engagement_controller import EngagementController
from strategies.hunter.hunter_mode_controller import HunterModeController
from strategies.movement.pathfinder import HexPathfinder
from strategies.movement.chase_tactics import ChaseTactics
from strategies.exploration.ruin_explorer import RuinExplorer
from strategies.inventory.equip_selector import EquipSelector
from strategies.inventory.inventory_manager import InventoryManager

from strategies.phases.early_game_strategy import EarlyGameStrategy
from strategies.phases.mid_game_strategy import MidGameStrategy
from strategies.phases.late_game_strategy import LateGameStrategy
from strategies.hazard.deadzone_warning_handler import DeadZoneWarningHandler
from strategies.hazard.deadzone_active_handler import DeadZoneActiveHandler


class DecisionEngine:
    def __init__(self, agent_name: str, game_state: GameState, dispatcher: ActionDispatcher):
        self.agent_name = agent_name
        self.game_state = game_state
        self.dispatcher = dispatcher
        
        self.logger = AgentLogger.get_logger(agent_name)
        
        self.analyzer = BattleAnalyzer(game_state)
        self.engagement = EngagementController(game_state)
        self.hunter = HunterModeController(game_state)
        self.pathfinder = HexPathfinder(game_state)
        self.chase = ChaseTactics(game_state)
        self.ruin_explorer = RuinExplorer(game_state)
        self.equip_selector = EquipSelector(game_state)
        self.inventory_manager = InventoryManager(game_state)

        self.early_strategy = EarlyGameStrategy(game_state)
        self.mid_strategy = MidGameStrategy(game_state)
        self.late_strategy = LateGameStrategy(game_state)
        self.deadzone_warning = DeadZoneWarningHandler(game_state)
        self.deadzone_active = DeadZoneActiveHandler(game_state)

        self.blocked_coordinates: Set[str] = set()
        self.deadzone_coordinates: Set[str] = set()

    async def execute_thought_cycle(self) -> None:
        """
        Executes one complete hierarchical decision/thought cycle [12].
        """
        bot_pos = self.game_state.current_region_id
        enemies_count = len(self.game_state.enemies)

        # 1. EVAKUASI DARURAT DEAD ZONE
        if self.deadzone_active.is_in_danger():
            if self.game_state.connections:
                escape_region = random.choice(self.game_state.connections)
                self.logger.critical(f"EMERGENCY EVACUATION: Escaping active Dead Zone from region {self.game_state.current_region_name} ({bot_pos}) to {escape_region} [14]!")
                await self.dispatcher.execute_move(escape_region)
            return

        # 2. PEMULIHAN MEDICAL FACILITY GRATIS
        current_facility = getattr(self.game_state, "current_facility", "")
        if current_facility == "Medical Facility" and self.game_state.hp < 70.0:
            self.logger.warning("TACTICAL DECISION: Standing on a Medical Facility. Initiating free healing interaction [11, 12].")
            await self.dispatcher.execute_interact()
            return

        # 3. KONTROL PERLENGKAPAN OTOMATIS (FREE ACTION)
        optimal_equip = self.equip_selector.determine_optimal_equips()
        if optimal_equip:
            item_id, slot_name = optimal_equip
            self.logger.warning(f"TACTICAL DECISION (Free Action): Equipping onto slot '{slot_name}' [9].")
            await self.dispatcher.execute_equip(item_id, slot_name)

        # 4. KONTROL LOOTING & PEMBERSIHAN TAS (FREE ACTION)
        inv_action, target_id, details_id = self.inventory_manager.determine_pickup_and_cleanup()
        if inv_action == "PICKUP" and target_id:
            # Tulis log pemungutan bersih hanya menggunakan tipe barang, menyembunyikan ID bising
            self.logger.info(f"TACTICAL DECISION (Free Action): Found valuable item. Initiating PICKUP of '{details_id}'.")
            await self.dispatcher.execute_pickup(target_id)
        elif inv_action == "DROP_AND_PICKUP" and target_id and details_id:
            # Cari nama barang lobi yang akan dibuang dari tas secara dinamis
            dropped_name = "Obsolete Item"
            for item in self.game_state.inventory:
                if item.get("id") == details_id:
                    dropped_name = item.get("type", "Obsolete Item")
                    break
            self.logger.info(f"TACTICAL DECISION (Free Action): Inventory full. Dropping '{dropped_name}' to PICKUP '{details_id}' [11].")
            await self.dispatcher.execute_equip(details_id, "drop")
            await self.dispatcher.execute_pickup(target_id)

        # 5. PEMICU PREDATOR GLOBAL (GLOBAL PREDATOR OVERRIDE)
        # Jika mendeteksi musuh sekarat atau peluang menang mutlak, bot langsung aktif mengejar
        # PROTEKSI MUTLAK: Bot dilarang melakukan PvP jika HP sekarat (<60%) atau tidak memegang senjata!
        battle_eval = self.analyzer.evaluate_combat_situation()
        if self.game_state.equipped_weapon and self.game_state.hp >= 60.0:
            if battle_eval.get("recommendation") == "FIGHT" and battle_eval.get("target"):
                enemy = battle_eval["target"]
                enemy_hp = float(enemy.get("hp", 100.0))
                win_rate = battle_eval.get("win_rate", 0.0)

                # Hanya kunci jika musuh terbukti hidup (0 < HP < 50) atau peluang menang mutlak (Win Rate >= 70)
                if 0.0 < enemy_hp < 50.0 or win_rate >= 0.70:
                    if not self.hunter.locked_target_id:
                        self.logger.warning(
                            f"PREDATOR LOCK INITIALIZED: Target {enemy.get('name')} in region {self.game_state.get_region_name(enemy.get('regionId'))} "
                            f"is highly vulnerable (HP: {enemy_hp}%, Win Rate: {win_rate:.1f}%). Overriding current phase strategy!"
                        )
                        self.hunter.lock_target(enemy)

        # 6. PENGAWAS STATUS KUNCI BURUAN (PENGAMAN KEMATIAN TARGET)
        # Jika target perburuan terdeteksi mati atau hilang dari sensor sekitar, segera lepaskan kunci target!
        if self.hunter.locked_target_id:
            locked_enemy_still_alive = False
            for p in self.game_state.enemies:
                if p.get("id") == self.hunter.locked_target_id:
                    locked_enemy_still_alive = True
                    break
            
            if not locked_enemy_still_alive:
                self.logger.warning(f"PREDATOR LOCK RELEASED: Target '{self.hunter.locked_target_name}' is dead or escaped. Releasing hunter lock!")
                self.hunter.release_target()

        # 7. PENANGANAN MOBS SEKITAR (MONSTER ENGAGEMENT RULE)
        # Mobs hanya diserang jika berada di wilayah kita, HP kita > 60%, dan kita memegang senjata
        if self.game_state.visible_monsters and self.game_state.hp > 60.0 and self.game_state.equipped_weapon:
            closest_mob = self.game_state.visible_monsters[0]
            mob_id = closest_mob.get("id")
            mob_name = closest_mob.get("name", "Monster")
            
            # Guardian tidak dilawan kecuali fullSet terpasang lengkap
            if "guardian" not in mob_name.lower() or self.game_state.has_full_set:
                self.logger.warning(f"PREY ALERT: Clearing hostile mob '{mob_name}' in current region [11].")
                await self.dispatcher.execute_attack(mob_id)
                return

        # 8. EVAKUASI DINI DEAD ZONE WARNING
        if self.deadzone_warning.is_warning_active():
            if self.game_state.connections:
                escape_region = random.choice(self.game_state.connections)
                resolved_escape_name = self.game_state.get_region_name(escape_region)
                self.logger.warning(f"TACTICAL DECISION: Dead Zone warning received. Evacuating early to safe region {resolved_escape_name} [14].")
                await self.dispatcher.execute_move(escape_region)
                return

        # 9. JALANKAN PERBURUAN AKTIF JIKA LOCK AKTIF
        if self.hunter.locked_target_id:
            if self.hunter.verify_hunt_safety(battle_eval):
                self.logger.info(f"HUNT STATUS: Hunter lock is active on player '{self.hunter.locked_target_name}'.")
                target_data = battle_eval["target"]
                distance = battle_eval["distance"]

                tactic, details = self.engagement.determine_spatial_tactic(target_data, distance)
                
                if tactic == "ATTACK":
                    self.logger.warning(f"COMBAT DISPATCH: Target '{self.hunter.locked_target_name}' is in range. Initiating attack action [11]!")
                    await self.dispatcher.execute_attack(self.hunter.locked_target_id)
                elif tactic == "APPROACH" and details:
                    t_region = target_data.get("regionId") or self.game_state.current_region_id
                    path = self.pathfinder.find_path(
                        start=bot_pos,
                        target=t_region,
                        blocked_coords=self.blocked_coordinates,
                        deadzone_coords=self.deadzone_coordinates
                    )
                    if path:
                        resolved_next_name = self.game_state.get_region_name(path[0])
                        resolved_target_name = self.game_state.get_region_name(t_region)
                        self.logger.warning(f"COMBAT APPROACH: Moving to connected region {resolved_next_name} to approach target '{self.hunter.locked_target_name}' in {resolved_target_name} [11].")
                        await self.dispatcher.execute_move(path[0])
                elif tactic == "RETREAT_TO_RANGE" and self.game_state.connections:
                    retreat_region = random.choice(self.game_state.connections)
                    resolved_retreat_name = self.game_state.get_region_name(retreat_region)
                    self.logger.warning(f"COMBAT RETREAT: Target entered melee range. Retreating to adjacent region {resolved_retreat_name} to recover weapon range [11].")
                    await self.dispatcher.execute_move(retreat_region)
                elif tactic == "REST":
                    self.logger.info("COMBAT REST: Insufficient EP to attack/move during chase. Rest initiated to restore EP.")
                    await self.dispatcher.execute_rest()
                return
            else:
                self.logger.warning("HUNT STATUS: Deactivating Hunter Mode. Safety check failed or target escaped.")
                self.hunter.release_target()

        # 10. JALANKAN LOGIKA PHASE-BASED KONDISIONAL (JIKA TIDAK SEDANG BERBURU)
        day = self.game_state.day
        if day == 1:
            action_type, details = self.early_strategy.determine_early_action()
            if action_type == "PICKUP" and details:
                await self.dispatcher.execute_pickup(details["item_id"])
            elif action_type == "EXPLORE":
                self.logger.info("TACTICAL DECISION: Standing on active ruins. Initiating ruin EXPLORE action [10].")
                await self.dispatcher.execute_explore()
            else:
                await self._navigate_to_nearest_ruins(bot_pos)
            return

        elif day == 2:
            action_type, target_data = self.mid_strategy.determine_mid_action(battle_eval)
            if action_type == "HUNT" and target_data:
                self.logger.warning(f"TACTICAL DECISION: Mid-game fight rating is high. Locking target '{target_data.get('name')}' for hunt [11]!")
                self.hunter.lock_target(target_data)
                await self.execute_thought_cycle()
            elif action_type == "EXPLORE":
                self.logger.info("TACTICAL DECISION: Standing on active ruins. Initiating ruin EXPLORE action [10].")
                await self.dispatcher.execute_explore()
            else:
                await self._navigate_to_nearest_ruins(bot_pos)
            return

        else:
            action_type, _ = self.late_strategy.determine_late_action(enemies_count)
            if action_type == "MOVE_TO_FOREST":
                await self._navigate_to_defensive_forest(bot_pos)
            elif action_type == "CONSERVE_REST":
                self.logger.info("TACTICAL DECISION: Rest initiated to conserve energy in safe forest area.")
                await self.dispatcher.execute_rest()
            else:
                if battle_eval.get("recommendation") == "FIGHT" and battle_eval.get("target"):
                    await self.dispatcher.execute_attack(battle_eval["target"].get("id"))
                else:
                    self.logger.info("TACTICAL DECISION: Conserving energy (Default Rest).")
                    await self.dispatcher.execute_rest()
            return

    async def _navigate_to_nearest_ruins(self, bot_pos: str) -> None:
        """Helper to find and pathfind to closest ruins on current visual map grid [10]."""
        if self.game_state.ep < 3.0:
            self.logger.info(f"TACTICAL DECISION: Low EP (Current: {self.game_state.ep}). Initiating rest to restore energy.")
            await self.dispatcher.execute_rest()
            return

        can_explore, _ = self.ruin_explorer.is_safe_to_explore()
        if can_explore:
            self.logger.info("TACTICAL DECISION: Standing on active ruins. Initiating EXPLORE action [10].")
            await self.dispatcher.execute_explore()
            return

        target_ruins_id = None
        for r in self.game_state.visible_ruins:
            if not r.get("isEmpty", False):
                target_ruins_id = r.get("ruinId")
                break

        if not target_ruins_id or not self.game_state.connections:
            # PENGAMAN MUTLAK: Gerakan jelajah acak mencari ruins ke salah satu connections tetangga (Anti-Freezing)
            if self.game_state.connections:
                random_region = random.choice(self.game_state.connections)
                resolved_random_name = self.game_state.get_region_name(random_region)
                self.logger.info(f"TACTICAL DECISION: No ruins in immediate vision. Moving randomly to adjacent region {resolved_random_name} to search.")
                await self.dispatcher.execute_move(random_region)
            return

        path = self.pathfinder.find_path(
            start=bot_pos,
            target=target_ruins_id,
            blocked_coords=self.blocked_coordinates,
            deadzone_coords=self.deadzone_coordinates
        )
        if path:
            resolved_next_name = self.game_state.get_region_name(path[0])
            resolved_ruins_name = self.game_state.get_region_name(target_ruins_id)
            self.logger.info(f"TACTICAL DECISION: Ruins detected in {resolved_ruins_name}. Pathfinder computed optimal path. Moving to next region {resolved_next_name} [10].")
            await self.dispatcher.execute_move(path[0])
        elif self.game_state.connections:
            random_region = random.choice(self.game_state.connections)
            resolved_random_name = self.game_state.get_region_name(random_region)
            self.logger.info(f"TACTICAL DECISION: Ruins blocked or unpathable. Moving randomly to adjacent region {resolved_random_name}.")
            await self.dispatcher.execute_move(random_region)

    async def _navigate_to_defensive_forest(self, bot_pos: str) -> None:
        """Helper to navigate to defense-boosting forest tiles (+3 DEF)."""
        if self.game_state.connections:
            random_region = random.choice(self.game_state.connections)
            resolved_random_name = self.game_state.get_region_name(random_region)
            self.logger.info(f"TACTICAL DECISION: Moving to adjacent defensive forest region {resolved_random_name} (+3 DEF).")
            await self.dispatcher.execute_move(random_region)