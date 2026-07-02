import aiohttp
import json
from logs.logs_network import (
    log_ws_connecting,
    log_ws_connected,
    log_ws_error,
    log_ws_send,
    log_ws_receive,
    log_ws_closed,
    log_ws_not_open_error
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
        self.last_logged_turn = -1

    async def connect(self, url: str) -> bool:
        log_ws_connecting(self.bot_name, url)
        try:
            self.session = aiohttp.ClientSession(headers=self.headers)
            self.ws = await self.session.ws_connect(url)
            log_ws_connected(self.bot_name)
            return True
        except Exception as e:
            log_ws_error(self.bot_name, str(e))
            return False

    async def send(self, data: dict):
        if self.ws:
            try:
                await self.ws.send_str(json.dumps(data))
                log_ws_send(self.bot_name, data)
            except Exception as e:
                log_ws_error(self.bot_name, str(e))
        else:
            log_ws_not_open_error(self.bot_name)

    async def receive(self):
        if not self.ws:
            return None
        try:
            msg = await self.ws.receive_str()
            log_ws_receive(self.bot_name, msg)
            frame = json.loads(msg)
            if isinstance(frame, dict):
                turn = frame.get("turn")
                msg_type = frame.get("type")
                is_alive = frame.get("view", {}).get("self", {}).get("isAlive", True)
                
                if (turn is not None and turn != self.last_logged_turn and msg_type in ("agent_view", "turn_advanced") and is_alive):
                    from logs.logs_gameplay import write_gameplay_log
                    write_gameplay_log(self.bot_name, f"# Turn {turn}", frame.get("view", {}))
                    self.last_logged_turn = turn
            return frame
        except Exception as e:
            log_ws_error(self.bot_name, str(e))
            return None

    async def close(self):
        if self.ws:
            await self.ws.close()
            log_ws_closed(self.bot_name)
        if self.session:
            await self.session.close()