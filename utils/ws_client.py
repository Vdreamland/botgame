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
    def __init__(self, api_key: str, bot_name: str, api_version: str = "1.12.0"):
        self.api_key = api_key
        self.bot_name = bot_name
        self.api_version = api_version
        self.headers = {
            "X-API-Key": self.api_key,
            "X-Version": self.api_version
        }
        self.session = None
        self.ws = None
        self.last_acted_turn = -1
        self.last_logged_turn = -1

    async def connect(self, url: str) -> bool:
        log_ws_connecting(self.bot_name, url)
        try:
            self.session = aiohttp.ClientSession(headers=self.headers)
            self.ws = await self.session.ws_connect(url, heartbeat=10.0)
            log_ws_connected(self.bot_name)
            return True
        except Exception as e:
            log_ws_error(self.bot_name, str(e))
            if self.session:
                await self.session.close()
                self.session = None
            return False

    async def send(self, payload: dict) -> bool:
        if not self.ws:
            return False
        try:
            raw_data = json.dumps(payload)
            log_ws_send(self.bot_name, raw_data)
            await self.ws.send_str(raw_data)
            return True
        except Exception as e:
            log_ws_error(self.bot_name, str(e))
            return False

    async def receive(self):
        if not self.ws:
            return None
        try:
            msg = await self.ws.receive()
            if msg.type == aiohttp.WSMsgType.TEXT:
                data_str = msg.data
                log_ws_receive(self.bot_name, data_str)
                frame = json.loads(data_str)
                return frame
            elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING):
                return None
            else:
                return None
        except Exception as e:
            log_ws_error(self.bot_name, str(e))
            return None

    async def close(self) -> None:
        try:
            if self.ws:
                await self.ws.close()
                log_ws_closed(self.bot_name)
        except Exception:
            pass
        finally:
            self.ws = None
            if self.session:
                await self.session.close()
                self.session = None