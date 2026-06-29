import asyncio
import json
import websockets
from typing import Dict, Any, Optional
from config import settings
from src.utils.logger import logger

class BaseWebSocketClient:
    """Base class to manage WebSocket connections to Claw Royale backend."""
    
    def __init__(self, url: str):
        self.url = url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._ping_task: Optional[asyncio.Task] = None
        self._is_active = False

    def _get_headers(self) -> Dict[str, str]:
        """Construct required Claw Royale headers."""
        return {
            "X-API-Key": settings.API_KEY,
            "X-Version": settings.X_VERSION
        }

    async def connect(self) -> bool:
        """Open WebSocket connection."""
        if self.websocket:
            await self.disconnect()
            
        logger.info(f"Connecting to: {self.url}")
        try:
            # Menggunakan parameter modern 'additional_headers' untuk kompatibilitas websockets v16.0
            self.websocket = await websockets.connect(
                self.url,
                additional_headers=self._get_headers()
            )
            self._is_active = True
            self._ping_task = asyncio.create_task(self._heartbeat_loop())
            logger.info("WebSocket connection opened successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {str(e)}")
            self.websocket = None
            return False

    async def disconnect(self):
        """Safely close WebSocket connection."""
        self._is_active = False
        if self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass
            self._ping_task = None

        if self.websocket:
            logger.info("Closing WebSocket...")
            await self.websocket.close()
            self.websocket = None
            logger.info("WebSocket closed safely.")

    async def send_json(self, payload: Dict[str, Any]):
        """Send JSON payload over socket."""
        if not self.websocket or not self._is_active:
            raise ConnectionError("WebSocket is inactive. Cannot send payload.")
        
        message = json.dumps(payload)
        await self.websocket.send(message)

    async def receive_json(self) -> Optional[Dict[str, Any]]:
        """Receive JSON payload from socket."""
        if not self.websocket or not self._is_active:
            raise ConnectionError("WebSocket is inactive. Cannot receive payload.")
        
        try:
            message = await self.websocket.recv()
            return json.loads(message)
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"Connection closed by server: Code {e.code}, Reason: {e.reason}")
            self._is_active = False
            return None
        except Exception as e:
            logger.error(f"Error receiving WebSocket payload: {str(e)}")
            return None

    async def _heartbeat_loop(self):
        """Keepalive heartbeat ping loop."""
        try:
            while self._is_active:
                await asyncio.sleep(15)
                if self.websocket and self._is_active:
                    await self.send_json({"type": "ping"})
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.debug(f"Heartbeat loop stopped: {str(e)}")