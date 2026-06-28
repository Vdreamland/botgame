# -*- coding: utf-8 -*-
"""
ClawRoyale Single Agent Instance.
Binds API Clients, WebSockets, State trackers, and Decision Engine into an active async loop [5, 8, 12, 13].
"""

import asyncio
from typing import Dict, Any

from utils.logger import AgentLogger
from utils.rate_limiter import TokenBucket
from core.network.api_client import APIClient
from core.network.ws_client import WebSocketClient
from core.state.game_state import GameState
from core.state.cooldown_manager import CooldownManager
from actions.action_dispatcher import ActionDispatcher
from brain.decision_engine import DecisionEngine
from core.lifecycle.runtime_manager import RuntimeManager


class AgentInstance:
    def __init__(self, agent_name: str, api_key: str, private_key: str, 
                 room_preference: str, rest_limiter: TokenBucket, ws_limiter: TokenBucket):
        self.agent_name = agent_name
        self.room_preference = room_preference
        self.logger = AgentLogger.get_logger(agent_name)
        
        base_http_url = "https://cdn.clawroyale.ai/api"
        base_ws_join = "wss://cdn.clawroyale.ai/ws/join"
        base_ws_agent = "wss://cdn.clawroyale.ai/ws/agent"

        self.api_client = APIClient(agent_name, api_key, base_http_url, rest_limiter)
        self.ws_client = WebSocketClient(agent_name, api_key, base_ws_join, base_ws_agent, ws_limiter)

        self.game_state = GameState(agent_name)
        self.cooldown_manager = CooldownManager(agent_name)

        self.dispatcher = ActionDispatcher(agent_name, self.ws_client, self.cooldown_manager)
        self.dispatcher.game_state = self.game_state
        
        self.decision_engine = DecisionEngine(agent_name, self.game_state, self.dispatcher)

        self.runtime = RuntimeManager(
            agent_name=agent_name,
            private_key=private_key,
            room_preference=room_preference,
            api_client=self.api_client,
            ws_client=self.ws_client
        )

        self.ws_client.on_message_callback = self._on_websocket_message

    async def start(self) -> None:
        self.logger.info(f"Launching Agent Instance for '{self.agent_name}'...")
        self.game_state.current_action = "MATCHMAKING QUEUE"
        await self.runtime.start()

    async def stop(self) -> None:
        self.logger.warning(f"Stopping Agent Instance for '{self.agent_name}'...")
        await self.runtime.stop()
        await self.api_client.close()
        self.game_state.clean_session_data()

    async def _on_websocket_message(self, message: Dict[str, Any]) -> None:
        """
        Processes incoming JSON frames from the WebSocket connection [5, 8, 12].
        """
        frame_type = message.get("type")
        
        self.logger.info(f"Raw WebSocket frame received: '{frame_type}'")
        
        # Validasi pembukaan tipe bingkai resmi pertempuran [8, 11, 12, 14]
        if frame_type not in ["agent_view", "turn_advanced", "can_act_changed", "deathzone_warning", "deathzone_expanded"]:
            return

        # Sinkronisasikan peta, HP, EP, dan musuh dari 'agent_view' atau 'turn_advanced' [8, 10, 11]
        self.game_state.update_from_server_frame(message)

        # Urai ketersediaan aksi dari tipe bingkai 'can_act_changed' [12]
        if frame_type == "can_act_changed":
            # Ekstrak bool canAct dari data payload [12]
            can_act_val = message.get("canAct", message.get("data", {}).get("canAct", True))
            self.cooldown_manager.update_server_can_act(bool(can_act_val))

        if self.ws_client.is_gameplay_active and self.game_state.current_action == "MATCHMAKING QUEUE":
            self.game_state.current_action = "ENTERING GAMEPLAY"

        # Picu pemikiran otonom jika canAct lokal terpenuhi [12]
        if (self.cooldown_manager.can_execute_action() and 
                self.ws_client.is_connected and 
                self.ws_client.is_gameplay_active):
            asyncio.create_task(self.decision_engine.execute_thought_cycle())