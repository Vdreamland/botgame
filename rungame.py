import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.agen_config import get_configured_bots, get_room_preference
from game.lobby_coordinator import LobbyCoordinator
from game.bot_lifecycle import run_bot_lifecycle
from utils.api_client import ClawRoyaleAPI
from utils.logger import logger

async def main():
    try:
        bots = get_configured_bots()
        room_preference = get_room_preference()

        if not bots:
            return

        bots_state = {}
        for bot in bots:
            bots_state[bot["name"]] = {
                "redeem": "Waiting",
                "smoltz": "Waiting",
                "target": room_preference.capitalize(),
                "room": "Waiting",
                "room_id": "",
                "alive": True,
                "status": "Waiting",
                "view": {},
            }

        logger.info("[*] Checking ongoing game profiles on startup...")
        bypass_lobby_on_startup = False
        for bot in bots:
            api_client = ClawRoyaleAPI(api_key=bot["api_key"])
            profile_res = await api_client.get_my_profile()
            if profile_res.get("success"):
                data = profile_res.get("data", {})
                current_games = data.get("currentGames", [])
                for g in current_games:
                    if g.get("isAlive") is True:
                        bypass_lobby_on_startup = True
                        break
            if bypass_lobby_on_startup:
                break

        coordinator = LobbyCoordinator(len(bots), bots_state)
        coordinator.bypass_lobby_on_startup = bypass_lobby_on_startup
        await coordinator.draw_table()

        tasks = [run_bot_lifecycle(bot, coordinator, room_preference) for bot in bots]

        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\nServer stopped manually.")
        os._exit(0)

if __name__ == "__main__":
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped manually.")
        os._exit(0)