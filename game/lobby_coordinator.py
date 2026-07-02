import asyncio
from logs.logs_agent import draw_status_table

class LobbyCoordinator:
    def __init__(self, total_bots: int, bots_state: dict):
        self.total_bots = total_bots
        self.bots_state = bots_state
        self.lobby = set()
        self.lobby_full = False
        self.exited_lobby = 0
        self.in_game = 0
        self.lock = asyncio.Lock()

    async def draw_table(self):
        draw_status_table(self.bots_state, self.total_bots)

    async def enter_lobby(self, bot_name: str):
        async with self.lock:
            self.lobby.add(bot_name)
            self.bots_state[bot_name]["status"] = "Waiting"
            self.bots_state[bot_name]["room"] = "Waiting"
            self.bots_state[bot_name]["room_id"] = ""
            self.bots_state[bot_name]["alive"] = True
            if len(self.lobby) == self.total_bots:
                self.lobby_full = True
                self.exited_lobby = 0
            await self.draw_table()

    async def wait_for_lobby(self, bot_name: str) -> bool:
        while not self.lobby_full:
            await asyncio.sleep(0.5)
        
        async with self.lock:
            self.exited_lobby += 1
            if self.exited_lobby == self.total_bots:
                self.lobby.clear()
                self.lobby_full = False
            return True

    async def leave_lobby(self, bot_name: str):
        async with self.lock:
            if bot_name in self.lobby:
                self.lobby.remove(bot_name)
            await self.draw_table()

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

    async def get_active_count(self, bot_name: str = None) -> int:
        async with self.lock:
            return self.in_game

    async def wait_for_cohort(self, bot_name: str = None, timeout: float = 120.0):
        start_time = asyncio.get_event_loop().time()
        while self.in_game > 0:
            if asyncio.get_event_loop().time() - start_time > timeout:
                break
            await asyncio.sleep(1.0)