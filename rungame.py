import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.agen_config import get_configured_bots, get_room_preference
from game.lobby_coordinator import LobbyCoordinator
from game.bot_lifecycle import run_bot_lifecycle

async def main():
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

    coordinator = LobbyCoordinator(len(bots), bots_state)
    await coordinator.draw_table()

    tasks = [run_bot_lifecycle(bot, coordinator, room_preference) for bot in bots]

    from web.server import start_web_server
    tasks.append(start_web_server(bots_state))

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped manually.")