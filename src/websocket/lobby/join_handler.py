import asyncio
from typing import Dict, Any, Optional
import websockets
from config import settings
from src.utils.logger import logger
from src.websocket.client import BaseWebSocketClient

class JoinHandler(BaseWebSocketClient):
    """Manages lobby matchmaking queue and assignment via /ws/join."""
    
    def __init__(self):
        super().__init__(settings.WS_JOIN_URL)

    async def execute_join_flow(self, entry_type: str = "free") -> Optional[websockets.WebSocketClientProtocol]:
        """Runs the queue joining protocol. Returns active socket upon game assignment."""
        connected = await self.connect()
        if not connected:
            logger.error("Failed to start matchmaking flow due to network issue.")
            return None

        try:
            # 2. Wait for welcome frame
            logger.info("Waiting for welcome frame from server...")
            welcome_frame = await self.receive_json()
            if not welcome_frame or welcome_frame.get("type") != "welcome":
                logger.error(f"Protocol mismatch. Expected 'welcome', received: {welcome_frame}")
                await self.disconnect()
                return None

            decision = welcome_frame.get("decision")
            logger.info(f"Initial decision: [ {decision} ]")

            # 3. Handle server decision
            if decision == "BLOCKED":
                logger.error("Access blocked. Please check account readiness flags at /accounts/me.")
                await self.disconnect()
                return None
                
            elif decision == "ALREADY_IN_GAME":
                logger.info("Active game detected. Proxying connection to arena...")
                active_socket = self.websocket
                self.websocket = None
                await self.disconnect()
                return active_socket

            # 4. Send hello handshake
            if entry_type == "free":
                logger.info("Queueing up for [ FREE ROOM ]")
                hello_payload = {
                    "type": "hello",
                    "entryType": "free"
                }
                await self.send_json(hello_payload)
            elif entry_type == "paid":
                logger.info("Queueing up for [ PAID ROOM ]")
                hello_payload = {
                    "type": "hello",
                    "entryType": "paid",
                    "mode": "offchain"
                }
                await self.send_json(hello_payload)
            else:
                logger.error(f"Unknown entry type: '{entry_type}'")
                await self.disconnect()
                return None

            # 5. Monitor queue until match is assigned
            logger.info("Waiting for room allocation (Matchmaking in progress)...")
            while self._is_active:
                response = await self.receive_json()
                if not response:
                    logger.error("Connection lost in matchmaking queue.")
                    break

                response_type = response.get("type")
                logger.info(f"Queue Status: {response}")

                if response_type == "sign_required":
                    logger.warning("EIP-712 signature required for Paid Room.")
                    logger.error("EIP-712 signing is not implemented. references/contracts.md is needed.")
                    break

                if response_type == "assigned" or response_type == "joined":
                    game_id = response.get("gameId")
                    agent_id = response.get("agentId")
                    logger.info(f"MATCHMAKING SUCCESSFUL! Assigned to Game ID: {game_id}, Agent ID: {agent_id}")
                    logger.info("Transitioning socket to gameplay...")
                    
                    active_socket = self.websocket
                    self.websocket = None
                    await self.disconnect()
                    return active_socket

                if response_type == "pong":
                    continue

        except Exception as e:
            logger.error(f"Error during matchmaking flow: {str(e)}")

        await self.disconnect()
        return None