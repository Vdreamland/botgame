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
        """
        Initializes the action coordinator for a single bot instance.
        """
        self.agent_name = agent_name
        self.ws_client = ws_client
        self.cooldown_manager = cooldown_manager
        self.logger = AgentLogger.get_logger(agent_name)

    async def _send_safe_cooldown_action(self, action_name: str, payload: Dict[str, Any]) -> bool:
        """
        Internal dispatcher helper. Enforces local cooldown check, transmits the package,
        and sets the local lock for 30s.
        """
        if not self.cooldown_manager.can_execute_action():
            remaining = self.cooldown_manager.get_remaining_cooldown()
            self.logger.warning(
                f"Action rejection: Tried to execute '{action_name}' but cooldown is still locked. "
                f"Remaining time: {remaining:.2f}s."
            )
            return False

        # Kirim payload lewat WebSocketClient (yang membatasi rate limit 120/menit) [13]
        await self.ws_client.send_message(payload)
        
        # Kunci lokal aksi ber-cooldown secepatnya setelah terkirim [12]
        self.cooldown_manager.set_action_cooldown(30.0)
        self.logger.info(f"Dispatched Cooldown Action: {action_name.upper()} (30s lock initiated).")
        return True

    # --- TRANSMITTER AKSI BER-COOLDOWN ---

    async def execute_move(self, q: int, r: int) -> bool:
        """Sends move command to hex (q, r)."""
        payload = CooldownActionFactory.create_move_payload(q, r)
        self.logger.info(f"Planning move execution to hex coordinates ({q}, {r}) [8].")
        return await self._send_safe_cooldown_action("move", payload)

    async def execute_explore(self) -> bool:
        """Sends explore ruins command [10]."""
        payload = CooldownActionFactory.create_explore_payload()
        self.logger.info("Planning ruin exploration execution [10].")
        return await self._send_safe_cooldown_action("explore", payload)

    async def execute_attack(self, target_id: str) -> bool:
        """Sends attack player/guardian command [11]."""
        payload = CooldownActionFactory.create_attack_payload(target_id)
        self.logger.warning(f"Planning attack execution on target ID: {target_id} [11].")
        return await self._send_safe_cooldown_action("attack", payload)

    async def execute_rest(self) -> bool:
        """Sends rest command to replenish energy."""
        payload = CooldownActionFactory.create_rest_payload()
        self.logger.info("Planning rest execution to replenish EP.")
        return await self._send_safe_cooldown_action("rest", payload)

    async def execute_interact(self) -> bool:
        """Sends interact command."""
        payload = CooldownActionFactory.create_interact_payload()
        self.logger.info("Planning environment interaction execution.")
        return await self._send_safe_cooldown_action("interact", payload)

    # --- TRANSMITTER AKSI BEBAS (FREE ACTIONS) ---

    async def execute_equip(self, item_id: str, slot: str) -> bool:
        """Sends equipment change command (no cooldown check required) [9, 13]."""
        payload = FreeActionFactory.create_equip_payload(item_id, slot)
        self.logger.info(f"Dispatched Free Action: EQUIP {slot.upper()} (Item ID: {item_id}).")
        await self.ws_client.send_message(payload)
        return True

    async def execute_pickup(self, item_id: str) -> bool:
        """Sends item grab command [13]."""
        payload = FreeActionFactory.create_pickup_payload(item_id)
        self.logger.info(f"Dispatched Free Action: PICKUP (Item ID: {item_id}).")
        await self.ws_client.send_message(payload)
        return True

    async def execute_whisper(self, target_id: str, message: str) -> bool:
        """Sends secure private message [13]."""
        payload = FreeActionFactory.create_whisper_payload(target_id, message)
        self.logger.info(f"Dispatched Free Action: WHISPER to ID {target_id}.")
        await self.ws_client.send_message(payload)
        return True

    async def execute_broadcast(self, message: str) -> bool:
        """Sends public broadcast message [13]."""
        payload = FreeActionFactory.create_broadcast_payload(message)
        self.logger.info(f"Dispatched Free Action: BROADCAST: '{message}'.")
        await self.ws_client.send_message(payload)
        return True