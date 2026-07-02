import asyncio
import aiohttp
import json
from logs.logs_network import (
    log_ws_connecting,
    log_ws_connected,
    log_ws_error,
    log_ws_send,
    log_ws_receive,
    log_ws_closed
)

class ClawRoyaleWSClient:
    def __init__(self, api_key: str, api_version: str = "1.12.0"):
        self.api_key = api_key
        self.api_version = api_version
        self.headers = {
            "X-API-Key": self.api_key,
            "X-Version": self.api_version
        }
        self.session = None
        self.ws = None

    async def connect(self, url: str) -> bool:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)
            
        try:
            log_ws_connecting(url)
            self.ws = await self.session.ws_connect(url, heartbeat=30.0)
            log_ws_connected()
            return True
        except Exception as e:
            log_ws_error(str(e))
            return False

    async def send(self, data: dict):
        if self.ws is not None and not self.ws.closed:
            try:
                await self.ws.send_json(data)
                log_ws_send(data)
            except Exception as e:
                log_ws_error(str(e))
        else:
            log_ws_error("Koneksi WebSocket belum dibuka atau terputus.")

    async def receive(self) -> dict:
        if self.ws is not None and not self.ws.closed:
            try:
                msg = await self.ws.receive()
                
                if msg.type == aiohttp.WSMsgType.TEXT:
                    log_ws_receive(msg.data)
                    return json.loads(msg.data)
                    
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    log_ws_closed()
                    return None
                    
            except Exception as e:
                log_ws_error(str(e))
                return None
        return None

    async def close(self):
        if self.ws is not None and not self.ws.closed:
            await self.ws.close()
            log_ws_closed()
            
        if self.session is not None and not self.session.closed:
            await self.session.close()