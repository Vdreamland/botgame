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
            if len(self.joined_bots) == 0:
                print("All bots queued. Waiting for match...")
                sys.stdout.flush()

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
                                        
                                elif msg_type in ("assigned", "waiting", "agent_view", "turn_advanced", "action_result"):
                                    await log_game.handle_message(self, bot_name, data, ws)
                                    if self.log_state.get("is_dead_break"):
                                        break
                                        
                                elif msg_type == "error":
                                    err_msg = data.get("message") or "Unknown server error"
                                    log_system.error(f"[{bot_name}] Lobby error: {err_msg}")
                                    break

                        # --- Penanganan Setelah Perulangan Pesan Selesai / Putus ---
                        
                        # Jika bot mati, keluar sepenuhnya dari perulangan utama (tidak re-antre)
                        if self.log_state.get("is_dead_break"):
                            break
                            
                        # Jika lobi di-block, tunggu sejenak lalu keluar sepenuhnya
                        if self.log_state.get("blocked_exit"):
                            await asyncio.sleep(5)
                            break
                            
                        # Log warning jika koneksi terputus dan lakukan proses pembersihan sebelum mencoba kembali
                        log_system.warning(f"[{bot_name}] Disconnected from game room.")
                        if bot_name in self.joined_bots:
                            self.joined_bots.remove(bot_name)
                            
                        while len(self.joined_bots) > 0:
                            await asyncio.sleep(1)
                            
                        await asyncio.sleep(5)

                # Cek kembali jika loop luar perlu dihentikan karena bot mati atau diblokir
                if self.log_state.get("is_dead_break") or self.log_state.get("blocked_exit"):
                    break

            except Exception as e:
                log_system.error(f"[{bot_name}] Connection failed: {str(e)}")
                if bot_name in self.joined_bots:
                    self.joined_bots.remove(bot_name)
                    
                while len(self.joined_bots) > 0:
                    await asyncio.sleep(1)
                    
                await asyncio.sleep(5)