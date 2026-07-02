import asyncio
from logs.logs_agent import draw_status_table

class LobbyCoordinator:
    def __init__(self, total_bots: int, bots_state: dict, max_batch_size: int = 80):
        self.total_bots = total_bots
        self.bots_state = bots_state
        self.max_batch_size = max_batch_size
        self.lobby = set()
        self.in_game = 0
        self.lock = asyncio.Lock()
        
        # Event untuk membuka pintu lobby bersamaan
        self.ready_event = asyncio.Event()
        self.timer_task = None

    async def draw_table(self):
        draw_status_table(self.bots_state, self.total_bots)

    async def _lobby_timer(self, delay: float):
        await asyncio.sleep(delay)
        self.ready_event.set()

    async def enter_lobby(self, bot_name: str):
        async with self.lock:
            self.lobby.add(bot_name)
            self.bots_state[bot_name]["status"] = "Waiting"
            self.bots_state[bot_name]["room"] = "Waiting"
            self.bots_state[bot_name]["room_id"] = ""
            self.bots_state[bot_name]["alive"] = True
            
            # Jika dia yang pertama masuk, mulai timer 10 detik
            if len(self.lobby) == 1:
                self.ready_event.clear()
                self.timer_task = asyncio.create_task(self._lobby_timer(10.0))
            
            # Jika lobby sudah penuh (max batch) atau semua bot terdaftar masuk
            if len(self.lobby) >= self.max_batch_size or len(self.lobby) == self.total_bots:
                if self.timer_task and not self.timer_task.done():
                    self.timer_task.cancel()
                self.ready_event.set()
                
            await self.draw_table()

    async def wait_for_lobby(self, bot_name: str) -> bool:
        # Menunggu sampai timer 10 detik habis ATAU kapasitas terpenuhi
        await self.ready_event.wait()
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