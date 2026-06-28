# -*- coding: utf-8 -*-
"""
ClawRoyale WebSocket Client.
Manages persistent connections for both the single queue (ws/join) and gameplay socket (ws/agent) [5].
"""

import json
import asyncio
import websockets
from typing import Dict, Any, Optional, Callable, Awaitable

from utils.logger import AgentLogger
from utils.rate_limiter import TokenBucket


class WebSocketClient:
    def __init__(self, agent_name: str, api_key: str, ws_join_url: str, ws_agent_url: str, ws_limiter: TokenBucket):
        self.agent_name = agent_name
        self.api_key = api_key
        self.ws_join_url = ws_join_url
        self.ws_agent_url = ws_agent_url
        self.ws_limiter = ws_limiter
        
        self.logger = AgentLogger.get_logger(agent_name)
        self.connection: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        self.is_gameplay_active = False
        
        self.on_message_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._listener_task: Optional[asyncio.Task] = None

    def _get_headers(self) -> Dict[str, str]:
        return {
            "X-Version": "1.11.2",
            "Authorization": f"mr-auth {self.api_key}"
        }

    async def _connect_with_fallback(self, url: str) -> websockets.WebSocketClientProtocol:
        headers = self._get_headers()
        try:
            return await websockets.connect(url, additional_headers=headers)
        except TypeError:
            return await websockets.connect(url, extra_headers=headers)

    async def connect_to_queue(self, room_preference: str) -> None:
        url = f"{self.ws_join_url}?version=1.11.2"
        self.logger.info(f"Connecting to Matchmaking Queue: {url}")
        
        try:
            self.connection = await self._connect_with_fallback(url)
            self.is_connected = True
            self.is_gameplay_active = False
            self.logger.info("Successfully connected to Matchmaking Queue.")
            
            self._heartbeat_task = asyncio.create_task(self._send_heartbeats())
            self._listener_task = asyncio.create_task(self._listen_loop(room_preference))
            
        except Exception as e:
            self.logger.error(f"WebSocket Queue Connection failed: {str(e)}")
            self.is_connected = False
            raise e

    async def connect_to_gameplay(self) -> None:
        """
        Connects directly to the ws/agent gameplay socket using authorized credentials [5].
        """
        await self.disconnect()
        
        url = self.ws_agent_url
        self.logger.info(f"Transitioning to Gameplay Socket: {url}")
        
        try:
            self.connection = await self._connect_with_fallback(url)
            self.is_connected = True
            self.is_gameplay_active = True
            self.logger.info("Successfully entered Gameplay Socket.")
            
            self._heartbeat_task = asyncio.create_task(self._send_heartbeats())
            self._listener_task = asyncio.create_task(self._listen_loop(None))
            
        except Exception as e:
            self.logger.error(f"WebSocket Gameplay Connection failed: {str(e)}")
            self.is_connected = False
            self.is_gameplay_active = False
            raise e

    async def send_message(self, payload: Dict[str, Any]) -> None:
        if not self.connection or not self.is_connected:
            self.logger.warning("Attempted to send message on closed socket. Aborting.")
            return

        await self.ws_limiter.consume(1.0)
        try:
            raw_msg = json.dumps(payload)
            await self.connection.send(raw_msg)
        except Exception as e:
            self.logger.error(f"Failed to transmit WebSocket message: {str(e)}")
            await self.disconnect()

    async def _send_heartbeats(self) -> None:
        try:
            while self.is_connected:
                await asyncio.sleep(5.0)
                await self.send_message({"type": "ping"})
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Heartbeat loop crashed: {str(e)}")

    async def _listen_loop(self, room_preference: Optional[str]) -> None:
        try:
            while self.is_connected:
                raw_msg = await self.connection.recv()
                data = json.loads(raw_msg)
                
                if data.get("type") == "welcome" and room_preference:
                    self.logger.info(f"Received 'welcome' frame. Joining with preference: {room_preference}")
                    await self.send_message({
                        "type": "hello",
                        "entryType": room_preference
                    })
                    continue
                
                if self.on_message_callback:
                    await self.on_message_callback(data)
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("WebSocket Connection closed by remote server.")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Listener loop encountered an error: {str(e)}")
        finally:
            await self.disconnect()

    async def disconnect(self) -> None:
        self.is_connected = False
        self.is_gameplay_active = False
        
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
            
        if self._listener_task:
            self._listener_task.cancel()
            self._listener_task = None
            
        if self.connection:
            try:
                await self.connection.close()
            except Exception:
                pass
            self.connection = None
            
        self.logger.info("WebSocket Client safely disconnected.")