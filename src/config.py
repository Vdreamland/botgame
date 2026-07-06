import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://cdn.clawroyale.ai"
WS_JOIN_URL = "wss://cdn.clawroyale.ai/ws/join"
VERSION = "1.12.0"

API_KEY = os.getenv("BOT1_API_KEY")
ROOM_PREFERENCE = os.getenv("ROOM_PREFERENCE", "free")

if not API_KEY:
    raise ValueError("BOT1_API_KEY is not configured in .env")

HEADERS = {
    "Authorization": f"mr-auth {API_KEY}",
    "X-Version": VERSION
}

def get_headers(api_key):
    return {
        "Authorization": f"mr-auth {api_key}",
        "X-Version": VERSION
    }

def get_all_bot_keys():
    keys = []
    for i in range(1, 11):
        key = os.getenv(f"BOT{i}_API_KEY")
        if key:
            keys.append((f"BOT{i}", key))
    if not keys and API_KEY:
        keys.append(("BOT1", API_KEY))
    return keys