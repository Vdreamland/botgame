# -*- coding: utf-8 -*-
"""
ClawRoyale Action Dispatcher.
Enforces local cooldown checks before dispatching and locks actions upon transmission.
"""

from typing import Dict, Any
from utils.logger import AgentLogger
from core.network.ws_client import WebSocketClient
from core.state.cooldown_manager import CooldownManager
from actions.cooldown_actions import CooldownActionFactory
from actions.free_actions import FreeActionFactory


class ActionDispatcher:
    def __init__(self, agent_name: str, ws_client: WebSocketClient, cooldown_manager: CooldownManager):
        self.agent_name = agent_name
        self.ws_client = ws_client
        self.cooldown_manager = cooldown_manager
        self.logger = AgentLogger.get_logger(agent_name)
        
        self.game_state = None

    async def _send_safe_cooldown_action(self, action_name: str, payload: Dict[str, Any]) -> bool:
        if not self.cooldown_manager.can_execute_action():
            remaining = self.cooldown_manager.get_remaining_cooldown()
            self.logger.warning(
                f"Action rejection: Tried to execute '{action_name}' but cooldown is still locked. "
                f"Remaining time: {remaining:.2f}s."
            )
            return False

        try:
            await self.ws_client.send_message(payload)
            self.cooldown_manager.set_action_cooldown(30.0)
            self.logger.info(f"Dispatched Cooldown Action: {action_name.upper()} (30s lock initiated).")
            return True
        except Exception as e:
            self.logger.error(f"Failed to transmit cooldown action '{action_name}': {str(e)}")
            return False

    async def execute_move(self, region_id: str) -> bool:
        # PENGAMAN GERAK CERDAS: Jangan kirim perintah jalan jika tujuan = tempat berdiri saat ini
        if self.game_state and self.game_state.current_region_id == region_id:
            self.logger.warning(f"Movement canceled: Bot is already standing in region {region_id}. Saving EP.")
            return False

        payload = CooldownActionFactory.create_move_payload(region_id)
        self.logger.info(f"Planning move execution to region ID: {region_id} [8].")
        
        if self.game_state:
            self.game_state.current_action = f"MOVING TO [{region_id}]"
            
        return await self._send_safe_cooldown_action("move", payload)

    async def execute_explore(self) -> bool:
        payload = CooldownActionFactory.create_explore_payload()
        self.logger.info("Planning ruin exploration execution [10].")
        
        if self.game_state:
            self.game_state.current_action = "EXPLORING RUINS"
            
        return await self._send_safe_cooldown_action("explore", payload)

    async def execute_attack(self, target_id: str) -> bool:
        payload = CooldownActionFactory.create_attack_payload(target_id)
        self.logger.warning(f"Planning attack execution on target ID: {target_id} [11].")
        
        if self.game_state:
            self.game_state.current_action = f"ATTACKING {target_id}"
            
        return await self._send_safe_cooldown_action("attack", payload)

    async def execute_rest(self) -> bool:
        payload = CooldownActionFactory.create_rest_payload()
        self.logger.info("Planning rest execution to replenish EP.")
        
        if self.game_state:
            self.game_state.current_action = "RESTING (EP RECOVERY)"
            
        return await self._send_safe_cooldown_action("rest", payload)

    async def execute_interact(self) -> bool:
        payload = CooldownActionFactory.create_interact_payload()
        self.logger.info("Planning environment interaction execution.")
        
        if self.game_state:
            self.game_state.current_action = "INTERACTING WITH FACILITY"
            
        return await self._send_safe_cooldown_action("interact", payload)

    async def execute_equip(self, item_id: str, slot: str) -> bool:
        payload = FreeActionFactory.create_equip_payload(item_id, slot)
        self.logger.info(f"Dispatched Free Action: EQUIP {slot.upper()} (Item ID: {item_id}).")
        
        if self.game_state:
            self.game_state.current_action = f"EQUIPPING {slot.upper()}"
            
        try:
            await self.ws_client.send_message(payload)
            return True
        except Exception as e:
            self.logger.error(f"Failed to transmit free action EQUIP: {str(e)}")
            return False

    async def execute_pickup(self, item_id: str) -> bool:
        payload = FreeActionFactory.create_pickup_payload(item_id)
        self.logger.info(f"Dispatched Free Action: PICKUP (Item ID: {item_id}).")
        
        if self.game_state:
            self.game_state.current_action = f"PICKING UP {item_id}"
            
        try:
            await self.ws_client.send_message(payload)
            return True
        except Exception as e:
            self.logger.error(f"Failed to transmit free action PICKUP: {str(e)}")
            return False

    async def execute_whisper(self, target_id: str, message: str) -> bool:
        payload = FreeActionFactory.create_whisper_payload(target_id, message)
        self.logger.info(f"Dispatched Free Action: WHISPER to ID {target_id}.")
        try:
            await self.ws_client.send_message(payload)
            return True
        except Exception as e:
            self.logger.error(f"Failed to transmit free action WHISPER: {str(e)}")
            return False

    async def execute_broadcast(self, message: str) -> bool:
        payload = FreeActionFactory.create_broadcast_payload(message)
        self.logger.info(f"Dispatched Free Action: BROADCAST: '{message}'.")
        try:
            await self.ws_client.send_message(payload)
            return True
        except Exception as e:
            self.logger.error(f"Failed to transmit free action BROADCAST: {str(e)}")
            return False