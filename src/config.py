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