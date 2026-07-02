import asyncio
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
            self.bots_state[bot_name]["status"] = "Waiting"
            self.bots_state[bot_name]["room"] = "Waiting"
            self.bots_state[bot_name]["room_id"] = ""
            self.bots_state[bot_name]["alive"] = True
        await self.draw_table()

    async def wait_for_lobby(self, bot_name: str) -> bool:
        while len(self.lobby) < self.total_bots:
            await asyncio.sleep(0.5)
        return True

    async def leave_lobby(self, bot_name: str):
        async with self.lock:
            if bot_name in self.lobby:
                self.lobby.remove(bot_name)

    async def enter_game(self, bot_name: str):
        async with self.lock:
            self.in_game += 1
            self.bots_state[bot_name]["status"] = "In Progress"
        await self.draw_table()

    async def leave_game(self, bot_name: str):
        async with self.lock:
            if self.in_game > 0:
                self.in_game -= 1
            self.bots_state[bot_name]["status"] = "Waiting"
            self.bots_state[bot_name]["room"] = "Waiting"
            self.bots_state[bot_name]["room_id"] = ""
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