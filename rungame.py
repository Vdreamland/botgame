import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.ws_client import ClawRoyaleWSClient
from utils.api_client import ClawRoyaleAPI
from utils.logger import logger
from config.agen_config import get_configured_bots, get_room_preference, auto_claim_rewards
from logs.logs_agent import draw_status_table

class LobbyCoordinator:
    def __init__(self, total_bots: int, bots_state: dict):
        self.total_bots = total_bots
        self.bots_state = bots_state
        self.lobby = set()
        self.in_game = 0
        self.lock = asyncio.Lock()

    async def draw_table(self):
        async with self.lock:
            draw_status_table(self.bots_state, self.total_bots)

    async def enter_lobby(self, bot_name: str):
        async with self.lock:
            self.lobby.add(bot_name)
            self.bots_state[bot_name]["status"] = "Lobby"
            self.bots_state[bot_name]["room"] = "Waiting"
        await self.draw_table()

    async def wait_for_lobby(self, bot_name: str, timeout: float = 10.0) -> bool:
        start_time = asyncio.get_event_loop().time()
        while len(self.lobby) < self.total_bots:
            if asyncio.get_event_loop().time() - start_time > timeout:
                return False
            await asyncio.sleep(0.5)
        return True

    async def leave_lobby(self, bot_name: str):
        async with self.lock:
            if bot_name in self.lobby:
                self.lobby.remove(bot_name)

    async def enter_game(self, bot_name: str):
        async with self.lock:
            self.in_game += 1
            self.bots_state[bot_name]["status"] = "In Game"
        await self.draw_table()

    async def leave_game(self, bot_name: str):
        async with self.lock:
            if self.in_game > 0:
                self.in_game -= 1
            self.bots_state[bot_name]["status"] = "Lobby"
            self.bots_state[bot_name]["room"] = "Waiting"
        await self.draw_table()

    async def get_active_count(self) -> int:
        async with self.lock:
            return self.in_game

    async def wait_for_cohort(self, timeout: float = 120.0):
        start_time = asyncio.get_event_loop().time()
        while self.in_game > 0:
            if asyncio.get_event_loop().time() - start_time > timeout:
                break
            await asyncio.sleep(1.0)

async def run_bot_lifecycle(bot_info: dict, coordinator: LobbyCoordinator, room_preference: str):
    bot_name = bot_info["name"]
    api_key = bot_info["api_key"]

    api_client = ClawRoyaleAPI(api_key=api_key)
    ws_client = ClawRoyaleWSClient(api_key=api_key, bot_name=bot_name)
    ws_url = "wss://cdn.clawroyale.ai/ws/join"

    while True:
        await auto_claim_rewards(api_client, bot_name, coordinator.bots_state, coordinator.draw_table)

        await coordinator.enter_lobby(bot_name)

        is_ready = await coordinator.wait_for_lobby(bot_name, 10.0)

        await coordinator.leave_lobby(bot_name)

        success = await ws_client.connect(ws_url)
        if success:
            await coordinator.enter_game(bot_name)

            try:
                welcome_frame = await ws_client.receive()
                if welcome_frame and welcome_frame.get("type") == "welcome":
                    decision = welcome_frame.get("decision")

                    if decision in ("ASK_ENTRY_TYPE", "FREE_ONLY"):
                        hello_payload = {
                            "type": "hello",
                            "entryType": room_preference,
                            "version": ws_client.api_version
                        }
                        await ws_client.send(hello_payload)

                        while True:
                            frame = await ws_client.receive()
                            if frame is None:
                                break

                            msg_type = frame.get("type")
                            if msg_type == "queued":
                                coordinator.bots_state[bot_name]["room"] = "Queue"
                                coordinator.bots_state[bot_name]["status"] = "Queued"
                                await coordinator.draw_table()
                            elif msg_type == "assigned":
                                match_id = frame.get("matchId") or "Room"
                                coordinator.bots_state[bot_name]["room"] = str(match_id)[:8]
                                coordinator.bots_state[bot_name]["status"] = "In Game"
                                await coordinator.draw_table()
                            elif msg_type == "error":
                                coordinator.bots_state[bot_name]["status"] = "Disconnect"
                                await coordinator.draw_table()
                                break
                    elif decision == "ALREADY_IN_GAME":
                        coordinator.bots_state[bot_name]["room"] = "Room"
                        coordinator.bots_state[bot_name]["status"] = "In Game"
                        await coordinator.draw_table()
                        while True:
                            frame = await ws_client.receive()
                            if frame is None:
                                break
                    else:
                        coordinator.bots_state[bot_name]["status"] = "Disconnect"
                        await coordinator.draw_table()
            except Exception:
                coordinator.bots_state[bot_name]["status"] = "Disconnect"
                await coordinator.draw_table()
            finally:
                await ws_client.close()
                await coordinator.leave_game(bot_name)

                active_count = await coordinator.get_active_count()
                if active_count > 0:
                    await coordinator.wait_for_cohort(120.0)
        else:
            coordinator.bots_state[bot_name]["status"] = "Retrying"
            await coordinator.draw_table()
            await asyncio.sleep(5.0)

async def main():
    bots = get_configured_bots()
    room_preference = get_room_preference()

    if not bots:
        logger.error("No active bots detected in configuration.")
        return

    bots_state = {}
    for bot in bots:
        bots_state[bot["name"]] = {
            "redeem": "Waiting",
            "weekly": "Waiting",
            "target": room_preference.capitalize(),
            "room": "Waiting",
            "status": "Waiting"
        }

    coordinator = LobbyCoordinator(len(bots), bots_state)
    await coordinator.draw_table()

    tasks = [run_bot_lifecycle(bot, coordinator, room_preference) for bot in bots]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())