# connection/socket_client.py

import asyncio
import aiohttp
import json
import sys
from connection.api_endpoints import WS_JOIN_URL
from connection.http_client import ClawRoyaleHTTPClient
from ui import log_system, log_game

class ClawRoyaleSocketClient:
    def __init__(self, api_key: str, version: str, room_preference: str = "free", joined_bots: list = None, total_bots: int = 0):
        self.api_key = api_key
        self.version = version
        self.room_preference = room_preference
        self.joined_bots = joined_bots if joined_bots is not None else []
        self.total_bots = total_bots
        self.log_state = {}
        self.consecutive_failures = 0  # Pelacak kegagalan koneksi beruntun untuk proteksi spam lobi

    async def connect_and_listen(self, bot_name: str, silent: bool = False):
        headers = {
            "X-API-Key": self.api_key,
            "X-Version": self.version
        }
        
        if silent:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(WS_JOIN_URL, headers=headers) as ws:
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                if data.get("type") == "welcome":
                                    await ws.close()
                                    return True
                            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                                return False
                        return False
            except Exception:
                return False

        while True:
            self.log_state.clear()

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(WS_JOIN_URL, headers=headers) as ws:
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                msg_type = data.get("type")
                                
                                if msg_type == "welcome":
                                    decision = data.get("decision")
                                    if decision in ("ASK_ENTRY_TYPE", "FREE_ONLY", "PAID_ONLY", "ALREADY_IN_GAME"):
                                        if decision != "ALREADY_IN_GAME":
                                            hello_frame = {"type": "hello", "entryType": self.room_preference}
                                            if self.room_preference == "paid":
                                                hello_frame["mode"] = "offchain"
                                            await ws.send_json(hello_frame)
                                    elif decision == "BLOCKED":
                                        log_system.error(f"[{bot_name}] Lobby entry blocked (check readiness conditions)")
                                        self.log_state["blocked_exit"] = True
                                        break
                                        
                                elif msg_type in ("assigned", "waiting", "agent_view", "turn_advanced", "action_result", "event", "game_ended"):
                                    self.consecutive_failures = 0  # Reset penghitung kegagalan jika ada pesan aktif lobi/room masuk
                                    await log_game.handle_message(self, bot_name, data, ws)
                                    if self.log_state.get("is_dead_break"):
                                        break
                                        
                                elif msg_type == "error":
                                    err_msg = data.get("message") or "Unknown server error"
                                    log_system.error(f"[{bot_name}] Lobby error: {err_msg}")
                                    break

                        # --- Penanganan Setelah Perulangan Pesan Selesai / Putus ---
                        
                        if self.log_state.get("is_dead_break"):
                            break
                            
                        if self.log_state.get("blocked_exit"):
                            await asyncio.sleep(5)
                            break
                        
                        close_code = ws.close_code
                        close_reason = "Unknown Disconnection"
                        is_genuine_failure = True
                        
                        if close_code is not None:
                            if close_code == 4000:
                                close_reason = "VERSION_MISMATCH (4000) - API version is outdated"
                            elif close_code == 4001:
                                close_reason = "READINESS_BLOCKED (4001) - Check sMoltz balance or active room lock"
                            elif close_code == 4003:
                                close_reason = "HELLO_TIMEOUT (4003) - Handshake hello frame timeout"
                            elif close_code == 4009:
                                close_reason = "ALREADY_IN_GAME (4009) - Agent is already active inside a running game"
                            elif close_code == 4503:
                                close_reason = "MAINTENANCE (4503) - Server is undergoing maintenance"
                            elif close_code == 1000:
                                close_reason = "not_selected / Cycle Close (1000) - Lobby cleared, waiting for next matchmaking cycle"
                                is_genuine_failure = False  # Normal lobi matchmaking, bukan kegagalan server
                            elif close_code == 1006:
                                close_reason = "Abnormal Close (1006) - Connection lost or dropped by server proxy"
                            else:
                                close_reason = f"Websocket Close Code {close_code}"

                        # Jika terdeteksi kode pemeliharaan server (4503), putuskan dan matikan koneksi instan
                        if close_code == 4503:
                            log_system.error(f"[{bot_name}] Server maintenance detected (Code 4503). Safely shutting down bot connection to prevent lobi spam.")
                            break

                        log_system.warning(f"[{bot_name}] Disconnected: {close_reason}")
                        
                        if bot_name in self.joined_bots:
                            self.joined_bots.remove(bot_name)

                        # Proteksi: Jika terjadi kegagalan beruntun murni (seperti proxy/jaringan mati) sebanyak 5 kali, matikan koneksi bot
                        if is_genuine_failure:
                            self.consecutive_failures += 1
                            if self.consecutive_failures >= 5:
                                log_system.error(f"[{bot_name}] Too many consecutive connection failures ({self.consecutive_failures}). Server might be offline. Safely terminating bot client.")
                                break
                            
                        await asyncio.sleep(5)

                if self.log_state.get("is_dead_break") or self.log_state.get("blocked_exit"):
                    break

            except Exception as e:
                log_system.error(f"[{bot_name}] Connection failed: {str(e)}")
                if bot_name in self.joined_bots:
                    self.joined_bots.remove(bot_name)
                    
                self.consecutive_failures += 1
                if self.consecutive_failures >= 5:
                    log_system.error(f"[{bot_name}] Too many consecutive connection failures ({self.consecutive_failures}). Safely terminating bot client to prevent server spam.")
                    break
                    
                await asyncio.sleep(5)