# connection/api_endpoints.py

BASE_URL = "https://cdn.clawroyale.ai/api"

VERSION_URL = f"{BASE_URL}/version"
ACCOUNTS_ME_URL = f"{BASE_URL}/accounts/me"
WS_JOIN_URL = "wss://cdn.clawroyale.ai/ws/join"
WS_AGENT_URL = "wss://cdn.clawroyale.ai/ws/agent"

# Loadout & Inventory Routes
LOADOUT_URL = f"{BASE_URL}/loadout"
LOADOUT_PACK_URL = f"{BASE_URL}/loadout/pack"
LOADOUT_SUB_URL = f"{BASE_URL}/loadout/sub"
LOADOUT_SLOT_URL = f"{BASE_URL}/loadout/slot"
INVENTORY_RELICS_URL = f"{BASE_URL}/inventory/relics"
INVENTORY_PACKS_URL = f"{BASE_URL}/inventory/packs"