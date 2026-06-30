import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "https://cdn.clawroyale.ai/api")
WS_JOIN_URL = os.getenv("WS_JOIN_URL", "wss://cdn.clawroyale.ai/ws/join")
WS_AGENT_URL = os.getenv("WS_AGENT_URL", "wss://cdn.clawroyale.ai/ws/agent")
X_VERSION = os.getenv("X_VERSION", "1.11.2")
ROOM_PREFERENCE = os.getenv("ROOM_PREFERENCE", "free").lower()

AGENT_NAME = os.getenv("BOT1_NAME", "ClawAgent").strip()
API_KEY = os.getenv("BOT1_API_KEY", "")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")

BOTS = []
num_bots = int(os.getenv("NUM_BOTS", "1"))
for i in range(1, num_bots + 1):
    name = os.getenv(f"BOT{i}_NAME", "").strip()
    api_key = os.getenv(f"BOT{i}_API_KEY", "").strip()
    if name and api_key:
        BOTS.append({
            "name": name,
            "api_key": api_key
        })

ALLY_NAMES = [bot["name"] for bot in BOTS]

# Global shared co-op databases
SHARED_LOOT_TARGETS = []
SOS_TARGETS = []
SHARED_VISITED_HISTORY = []
SHARED_ACTIVE_DEATHZONES = []
BOT_POSITIONS = {}

# Tracks active battle status for each bot to synchronize matchmaking
ACTIVE_BOTS_IN_GAME = {bot["name"]: False for bot in BOTS}

def validate_config():
    """Validate critical configurations."""
    if not BOTS:
        raise ValueError("Configuration error: BOTS list is empty. Check NUM_BOTS in .env.")
    
    for i, bot in enumerate(BOTS, 1):
        if not bot["api_key"]:
            raise ValueError(f"Configuration error: API_KEY for BOT{i} is missing in .env.")
        if not bot["name"]:
            raise ValueError(f"Configuration error: Name for BOT{i} is missing in .env.")
            
    if ROOM_PREFERENCE not in ["free", "paid"]:
        raise ValueError(f"Configuration error: ROOM_PREFERENCE '{ROOM_PREFERENCE}' is invalid. Use 'free' or 'paid'.")