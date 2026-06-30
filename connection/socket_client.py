# connection/socket_client.py

import asyncio
import aiohttp
import json
from connection.api_endpoints import WS_JOIN_URL
from ui import log_connection as log

class ClawRoyaleSocketClient:
    def __init__(self, api_key: str, version: str, room_preference: str = "free"):
        self.api_key = api_key
        self.version = version
        self.room_preference = room_preference

    async def connect_and_listen(self, bot_name: str, silent: bool = False):
        headers = {
            "X-API-Key": self.api_key,
            "X-Version": self.version
        }
        
        if not silent:
            log.bot_info(bot_name, "Connecting to WebSocket: /ws/join")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(WS_JOIN_URL, headers=headers) as ws:
                    if not silent:
                        log.bot_success(bot_name, "WebSocket connected successfully.")
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            
                            if data.get("type") == "welcome":
                                await ws.close()
                                if not silent:
                                    log.bot_success(bot_name, "WebSocket disconnected immediately as requested.")
                                return True
                                
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            if not silent:
                                log.bot_warning(bot_name, "WebSocket disconnected unexpectedly.")
                            return False
                    return False
        except Exception as e:
            if not silent:
                log.bot_error(bot_name, f"WebSocket error: {str(e)}")
            return False