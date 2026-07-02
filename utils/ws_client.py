import aiohttp
import json
import logging
from logs.logs_network import (
    log_ws_connecting,
    log_ws_connected,
    log_ws_error,
    log_ws_send,
    log_ws_receive,
    log_ws_closed
)

logger = logging.getLogger("WSClient")

class ClawRoyaleWSClient:
    def __init__(self, api_key: str, api_version: str = "1.12.0"):
        self.api_key = api_key
        self.api_version = api_version
        self.headers = {
            "X-API-Key": self.api_key,
            "X-Version": self.api_version
        }
        self.ws = None

    async def connect(self, url: str) -> bool:
        log_ws_connecting(url)
        try:
            session = aiohttp.ClientSession(headers=self.headers)
            self.ws = await session.ws_connect(url)
            log_ws_connected()
            return True
        except Exception as e:
            log_ws_error(str(e))
            return False

    async def send(self, data: dict):
        if self.ws:
            try:
                await self.ws.send_str(json.dumps(data))
                log_ws_send(data)
            except Exception as e:
                log_ws_error(str(e))
        else:
            log_ws_error("WebSocket connection is not open or has been disconnected.")

    async def receive(self):
        if not self.ws:
            return None
        try:
            msg = await self.ws.receive_str()
            log_ws_receive(msg)
            return json.loads(msg)
        except Exception as e:
            log_ws_error(str(e))
            return None

    async def close(self):
        if self.ws:
            await self.ws.close()
            log_ws_closed()