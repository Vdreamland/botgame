# connection/socket_client.py

import asyncio
import aiohttp
import json
import sys
from connection.api_endpoints import WS_JOIN_URL
from ui import log_system, log_game

class ClawRoyaleSocketClient:
    def __init__(self, api_key: str, version: str, room_preference: str = "free", joined_bots: list = None, total_bots: int = 0):
        self.api_key = api_key
        self.version = version
        self.room_preference = room_preference
        self.joined_bots = joined_bots if joined_bots is not None else []
        self.total_bots = total_bots

    async def _fetch_room_name(self, game_id: str) -> str:
        url = f"https://cdn.clawroyale.ai/api/games/{game_id}"
        headers = {
            "X-API-Key": self.api_key,
            "X-Version": self.version
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as r:
                    if r.status == 200:
                        res = await r.json()
                        if isinstance(res, dict) and res.get("success"):
                            data = res.get("data", {})
                            name = data.get("name") or data.get("title")
                            if name:
                                return name
        except Exception:
            pass
        return game_id[:8]

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
            current_status = None
            resolved_room_name = None
            is_active_logged = False
            last_printed_turn = -1
            
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
                                        await asyncio.sleep(5)
                                        break
                                        
                                elif msg_type in ("assigned", "waiting"):
                                    if not is_active_logged:
                                        is_active_logged = True
                                        if bot_name not in self.joined_bots:
                                            self.joined_bots.append(bot_name)
                                            if len(self.joined_bots) == self.total_bots:
                                                print("All bots successfully joined room!")
                                                print()
                                                sys.stdout.flush()
                                                
                                elif msg_type in ("agent_view", "turn_advanced", "action_result"):
                                    if not is_active_logged:
                                        is_active_logged = True
                                        if bot_name not in self.joined_bots:
                                            self.joined_bots.append(bot_name)
                                            if len(self.joined_bots) == self.total_bots:
                                                print("All bots successfully joined room!")
                                                print()
                                                sys.stdout.flush()
                                    
                                    view = data.get("view") or data.get("data", {}).get("view") or {}
                                    self_data = view.get("self", {})
                                    current_region = view.get("currentRegion", {})
                                    turn = data.get("turn") or view.get("turn") or 1
                                    
                                    is_alive = self_data.get("isAlive", True)
                                    if self_data.get("hp", 100) <= 0:
                                        is_alive = False
                                    
                                    if turn != last_printed_turn:
                                        while len(self.joined_bots) < self.total_bots:
                                            await asyncio.sleep(0.5)

                                        game_id = data.get("gameId") or view.get("gameId") or ""
                                        if not resolved_room_name:
                                            resolved_room_name = await self._fetch_room_name(game_id)
                                            
                                        await log_game.print_turn_log(
                                            bot_name=bot_name,
                                            api_key=self.api_key,
                                            version=self.version,
                                            game_id=game_id,
                                            turn=turn,
                                            self_data=self_data,
                                            current_region=current_region,
                                            view_data=view,
                                            resolved_room_name=resolved_room_name
                                        )
                                        last_printed_turn = turn
                                        
                                    if not is_alive:
                                        if bot_name in self.joined_bots:
                                            self.joined_bots.remove(bot_name)
                                        log_system.warning(f"[{bot_name}] Dead. Waiting for other bots to finish...")
                                        await ws.close()
                                        
                                        while len(self.joined_bots) > 0:
                                            await asyncio.sleep(1)
                                            
                                        await asyncio.sleep(5)
                                        break
                                        
                                elif msg_type == "error":
                                    err_msg = data.get("message") or "Unknown server error"
                                    log_system.error(f"[{bot_name}] Lobby error: {err_msg}")
                                    await asyncio.sleep(5)
                                    break
                                    
                            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                                log_system.warning(f"[{bot_name}] Disconnected from game room.")
                                if bot_name in self.joined_bots:
                                    self.joined_bots.remove(bot_name)
                                    
                                while len(self.joined_bots) > 0:
                                    await asyncio.sleep(1)
                                    
                                await asyncio.sleep(5)
                                break
            except Exception as e:
                log_system.error(f"[{bot_name}] Connection failed: {str(e)}")
                if bot_name in self.joined_bots:
                    self.joined_bots.remove(bot_name)
                    
                while len(self.joined_bots) > 0:
                    await asyncio.sleep(1)
                    
                await asyncio.sleep(5)