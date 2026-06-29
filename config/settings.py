import os
from dotenv import load_dotenv

# Memuat berkas .env
load_dotenv()

API_URL = os.getenv("API_URL", "https://cdn.clawroyale.ai/api")
WS_JOIN_URL = os.getenv("WS_JOIN_URL", "wss://cdn.clawroyale.ai/ws/join")
WS_AGENT_URL = os.getenv("WS_AGENT_URL", "wss://cdn.clawroyale.ai/ws/agent")
X_VERSION = os.getenv("X_VERSION", "1.11.2")

# Kredensial Utama Bot
API_KEY = os.getenv("API_KEY", "")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")

def validate_config():
    """Memvalidasi kelengkapan konfigurasi kritis sebelum menjalankan bot."""
    if not API_KEY:
        raise ValueError("Error: API_KEY tidak ditemukan di file .env. Bot membutuhkan API_KEY untuk terhubung.")