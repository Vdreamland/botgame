import os
from dotenv import load_dotenv

load_dotenv()

def get_configured_bots() -> list:
    num_bots = int(os.getenv("NUM_BOTS", 1))
    bots = []
    for i in range(1, num_bots + 1):
        name = os.getenv(f"BOT{i}_NAME")
        api_key = os.getenv(f"BOT{i}_API_KEY")
        if name and api_key:
            bots.append({"name": name, "api_key": api_key})
    return bots

def get_room_preference() -> str:
    return os.getenv("ROOM_PREFERENCE", "free")