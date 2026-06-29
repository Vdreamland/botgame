import asyncio
from typing import Dict, Any, Optional, Tuple
import websockets
from config import settings
from src.utils.logger import logger
from src.websocket.client import BaseWebSocketClient

class JoinHandler(BaseWebSocketClient):
    """Manages lobby matchmaking queue and assignment via /ws/join."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(settings.WS_JOIN_URL, api_key)

    async def execute_join_flow(self, entry_type: str = "free") -> Tuple[Optional[websockets.WebSocketClientProtocol], bool]:
        """Runs the queue joining protocol. Returns (socket, is_new_game)."""
        connected = await self.connect()
        if not connected:
            logger.error("Failed to start matchmaking flow due to network issue.")
            return None, False

        try:
            logger.info("Waiting for welcome frame from server...")
            welcome_frame = await self.receive_json()
            if not welcome_frame or welcome_frame.get("type") != "welcome":
                logger.error(f"Protocol mismatch. Expected 'welcome', received: {welcome_frame}")
                await self.disconnect()
                return None, False

            decision = welcome_frame.get("decision")
            logger.info(f"Initial decision: [ {decision} ]")

            if decision == "BLOCKED":
                logger.error("Access blocked. Please check account readiness flags at /accounts/me.")
                await self.disconnect()
                return None, False
                
            elif decision == "ALREADY_IN_GAME":
                logger.info("Active game detected. Proxying connection to arena...")
                active_socket = self.websocket
                self.websocket = None
                await self.disconnect()
                return active_socket, False

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
                return None, False

            logger.info("Waiting for room allocation (Matchmaking in progress)...")
            while self._is_active:
                response = await self.receive_json()
                if not response:
                    logger.error("Connection lost in matchmaking queue.")
                    break

                response_type = response.get("type")
                
                if response_type == "queued":
                    logger.info("Still in queue, waiting for players...")
                    continue

                if response_type == "sign_required":
                    logger.warning("EIP-712 signature required for Paid Room.")
                    logger.error("EIP-712 signing is not implemented. references/contracts.md is needed.")
                    break

                if response_type == "assigned" or response_type == "joined":
                    logger.info("Matchmaking successful! Entering battle arena...")
                    
                    active_socket = self.websocket
                    self.websocket = None
                    await self.disconnect()
                    return active_socket, True

                if response_type == "pong":
                    continue

        except Exception as e:
            logger.error(f"Error during matchmaking flow: {str(e)}")

        await self.disconnect()
        return None, False