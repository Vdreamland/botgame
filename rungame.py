import asyncio
from utils.ws_client import ClawRoyaleWSClient
from utils.api_client import ClawRoyaleAPI
from utils.logger import logger
from config.agent_config import get_configured_bots, get_room_preference
from logs.logs_network import (
    log_matchmaking_queued,
    log_match_assigned,
    log_matchmaking_failed,
    log_connection_failed
)
from logs.logs_agent import (
    log_orchestrator_start,
    log_bot_detected,
    log_orchestrator_target,
    log_bot_lobby_wait,
    log_bot_lobby_ready,
    log_bot_game_start,
    log_bot_game_ended,
    log_bot_waiting_cohort
)

class LobbyCoordinator:
    def __init__(self, total_bots: int):
        self.total_bots = total_bots
        self.lobby = set()
        self.in_game = 0
        self.lock = asyncio.Lock()

    async def enter_lobby(self, bot_name: str):
        async with self.lock:
            self.lobby.add(bot_name)

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

    async def enter_game(self):
        async with self.lock:
            self.in_game += 1

    async def leave_game(self):
        async with self.lock:
            if self.in_game > 0:
                self.in_game -= 1

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
    ws_client = ClawRoyaleWSClient(api_key=api_key)
    ws_url = "wss://cdn.clawroyale.ai/ws/join"

    while True:
        await api_client.auto_claim_rewards()

        await coordinator.enter_lobby(bot_name)
        log_bot_lobby_wait(bot_name)

        is_ready = await coordinator.wait_for_lobby(bot_name, 10.0)
        if is_ready:
            log_bot_lobby_ready()

        await coordinator.leave_lobby(bot_name)

        success = await ws_client.connect(ws_url)
        if success:
            await coordinator.enter_game()
            log_bot_game_start(bot_name)

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
                                log_matchmaking_queued()
                            elif msg_type == "assigned":
                                log_match_assigned()
                            elif msg_type == "error":
                                error_msg = frame.get("message") or "Unknown error"
                                log_matchmaking_failed(error_msg)
                                break
                    elif decision == "ALREADY_IN_GAME":
                        logger.info(f"[{bot_name}] Reconnected successfully to active game session.")
                        while True:
                            frame = await ws_client.receive()
                            if frame is None:
                                break
                    else:
                        log_matchmaking_failed(f"Server decision: {decision}")
            except Exception as e:
                logger.error(f"[{bot_name}] Error in game session: {str(e)}")
            finally:
                await ws_client.close()
                await coordinator.leave_game()
                log_bot_game_ended(bot_name)

                active_count = await coordinator.get_active_count()
                if active_count > 0:
                    log_bot_waiting_cohort(bot_name, active_count)
                    await coordinator.wait_for_cohort(120.0)
        else:
            log_connection_failed()
            await asyncio.sleep(5.0)

async def main():
    bots = get_configured_bots()
    room_preference = get_room_preference()

    if not bots:
        logger.error("No active bots detected in configuration.")
        return

    log_orchestrator_start(len(bots))
    for bot in bots:
        log_bot_detected(bot["name"])
    log_orchestrator_target(room_preference)

    coordinator = LobbyCoordinator(len(bots))
    tasks = [run_bot_lifecycle(bot, coordinator, room_preference) for bot in bots]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())