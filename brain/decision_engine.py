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
from strategies.movement.pathfinder import HexPathfinder, HEX_NEIGHBORS
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

        self.blocked_coordinates: Set[Tuple[int, int]] = set()
        self.deadzone_coordinates: Set[Tuple[int, int]] = set()

    async def execute_thought_cycle(self) -> None:
        """
        Executes one complete hierarchical decisionthought cycle [12].
        """
        bot_pos = (self.game_state.q, self.game_state.r)

        if self.deadzone_active.is_in_danger():
            self.logger.critical("EMERGENCY: Agent is inside the active Dead Zone! Overriding strategies [14].")
            safe_center = (0, 0) 
            response_type, details = self.deadzone_active.determine_emergency_response(
                safe_escape_coord=safe_center,
                blocked_coords=self.blocked_coordinates,
                active_deadzone_coords=self.deadzone_coordinates
            )

            if response_type == "EMERGENCY_HEAL" and details:
                await self.dispatcher.execute_equip(details["item_id"], "use")
            elif response_type == "EMERGENCY_MOVE" and details:
                nq, nr = details
                await self.dispatcher.execute_move(nq, nr)
            return

        current_facility = getattr(self.game_state, "current_facility", "")
        if current_facility == "Medical Facility" and self.game_state.hp < 70.0:
            self.logger.warning("Standing on a Medical Facility. Initiating free healing interaction [11, 12].")
            await self.dispatcher.execute_interact()
            return

        optimal_equip = self.equip_selector.determine_optimal_equips()
        if optimal_equip:
            item_id, slot_name = optimal_equip
            self.logger.warning(f"Optimization trigger: Equipping {item_id} onto slot '{slot_name}' [9].")
            await self.dispatcher.execute_equip(item_id, slot_name)

        inv_action, target_id, details_id = self.inventory_manager.determine_pickup_and_cleanup()
        if inv_action == "PICKUP" and target_id:
            await self.dispatcher.execute_pickup(target_id)
        elif inv_action == "DROP_AND_PICKUP" and target_id and details_id:
            await self.dispatcher.execute_equip(details_id, "drop")
            await self.dispatcher.execute_pickup(target_id)

        if self.deadzone_warning.is_warning_active():
            self.logger.warning("Dead Zone warning received. Day 2 expansion is imminent [14].")
            safe_center = (0, 0)
            escape_path = self.deadzone_warning.calculate_evacuation_path(
                safe_center_coord=safe_center,
                blocked_coords=self.blocked_coordinates,
                active_deadzone_coords=self.deadzone_coordinates
            )
            if escape_path:
                nq, nr = escape_path[0]
                self.logger.warning(f"Evacuating early towards safe zone coordinates ({nq}, {nr}) [14].")
                await self.dispatcher.execute_move(nq, nr)
                return

        battle_eval = self.analyzer.evaluate_combat_situation()
        enemies_count = len(self.game_state.enemies)

        if self.hunter.locked_target_id:
            if self.hunter.verify_hunt_safety(battle_eval):
                self.logger.info(f"Target lock active on player: {self.hunter.locked_target_name}.")
                target_data = battle_eval["target"]
                distance = battle_eval["distance"]

                tactic, details = self.engagement.determine_spatial_tactic(target_data, distance)
                
                if tactic == "ATTACK":
                    await self.dispatcher.execute_attack(self.hunter.locked_target_id)
                elif tactic == "APPROACH" and details:
                    t_coord = details["target_coords"]
                    path = self.pathfinder.find_path(
                        start=bot_pos,
                        target=t_coord,
                        blocked_coords=self.blocked_coordinates,
                        deadzone_coords=self.deadzone_coordinates
                    )
                    if path:
                        nq, nr = path[0]
                        await self.dispatcher.execute_move(nq, nr)
                elif tactic == "RETREAT_TO_RANGE":
                    await self.dispatcher.execute_move(bot_pos[0] - 1, bot_pos[1])
                elif tactic == "REST":
                    await self.dispatcher.execute_rest()
                return
            else:
                self.logger.warning("Hunter Mode deactivated. Target escaped or HP dropped to critical limit.")
                self.hunter.release_target()

        day = self.game_state.day
        if day == 1:
            action_type, details = self.early_strategy.determine_early_action()
            if action_type == "PICKUP" and details:
                await self.dispatcher.execute_pickup(details["item_id"])
            elif action_type == "EXPLORE":
                await self.dispatcher.execute_explore()
            else:
                await self._navigate_to_nearest_ruins(bot_pos)
            return

        elif day == 2:
            action_type, target_data = self.mid_strategy.determine_mid_action(battle_eval)
            if action_type == "HUNT" and target_data:
                self.logger.warning(f"Locking target: {target_data.get('name')} for combat initiation!")
                self.hunter.lock_target(target_data)
                await self.execute_thought_cycle()
            elif action_type == "EXPLORE":
                await self.dispatcher.execute_explore()
            else:
                await self._navigate_to_nearest_ruins(bot_pos)
            return

        else:
            action_type, _ = self.late_strategy.determine_late_action(enemies_count)
            if action_type == "MOVE_TO_FOREST":
                await self._navigate_to_defensive_forest(bot_pos)
            elif action_type == "CONSERVE_REST":
                await self.dispatcher.execute_rest()
            else:
                if battle_eval.get("recommendation") == "FIGHT" and battle_eval.get("target"):
                    await self.dispatcher.execute_attack(battle_eval["target"].get("id"))
                else:
                    await self.dispatcher.execute_rest()
            return

    async def _navigate_to_nearest_ruins(self, bot_pos: Tuple[int, int]) -> None:
        """Helper to find and pathfind to closest ruins on current visual map grid [10]."""
        if self.game_state.ep < 3.0:
            await self.dispatcher.execute_rest()
            return

        # Cek kelayakan: jika berdiri di atas ruins, langsung explore [10]
        can_explore, _ = self.ruin_explorer.is_safe_to_explore()
        if can_explore:
            await self.dispatcher.execute_explore()
            return

        # Cari koordinat ruins dinamis yang terdeteksi di sekitar
        target_ruins = None
        
        # Pindai item di tanah untuk mencari tile penanda ruins/s-relic [10]
        for item in self.game_state.items_on_ground:
            if item.get("type") in ["ruins", "s-relic"]:
                target_ruins = (int(item.get("q", 0)), int(item.get("r", 0)))
                break

        if not target_ruins:
            # PENGAMAN MUTLAK: Jika tidak mendeteksi ruins di sensor sekitar,
            # lakukan gerakan jelajah acak mencari ruins (Anti-Freezing) [12].
            dq, dr = random.choice(HEX_NEIGHBORS)
            await self.dispatcher.execute_move(bot_pos[0] + dq, bot_pos[1] + dr)
            return

        path = self.pathfinder.find_path(
            start=bot_pos,
            target=target_ruins,
            blocked_coords=self.blocked_coordinates,
            deadzone_coords=self.deadzone_coordinates
        )
        if path:
            nq, nr = path[0]
            await self.dispatcher.execute_move(nq, nr)
        else:
            await self.dispatcher.execute_rest()

    async def _navigate_to_defensive_forest(self, bot_pos: Tuple[int, int]) -> None:
        """Helper to navigate to defense-boosting forest tiles (+3 DEF)."""
        # Jelajah acak untuk mencari ubin Forest
        dq, dr = random.choice(HEX_NEIGHBORS)
        await self.dispatcher.execute_move(bot_pos[0] + dq, bot_pos[1] + dr)