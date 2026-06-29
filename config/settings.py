import os
from dotenv import load_dotenv

# Memuat berkas .env
load_dotenv()

API_URL = os.getenv("API_URL", "https://cdn.clawroyale.ai/api")
WS_JOIN_URL = os.getenv("WS_JOIN_URL", "wss://cdn.clawroyale.ai/ws/join")
WS_AGENT_URL = os.getenv("WS_AGENT_URL", "wss://cdn.clawroyale.ai/ws/agent")
X_VERSION = os.getenv("X_VERSION", "1.11.2")

# Preferensi Room ("free" atau "paid")
ROOM_PREFERENCE = os.getenv("ROOM_PREFERENCE", "free").lower()

# Nama Identitas Agen Bot
AGENT_NAME = os.getenv("AGENT_NAME", "ClawAgent").strip()

# Kredensial Utama Bot
API_KEY = os.getenv("API_KEY", "")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")

def validate_config():
    """Memvalidasi kelengkapan konfigurasi kritis sebelum menjalankan bot."""
    if not API_KEY:
        raise ValueError("Error: API_KEY tidak ditemukan di file .env. Bot membutuhkan API_KEY untuk terhubung.")
    
    if ROOM_PREFERENCE not in ["free", "paid"]:
        raise ValueError(f"Error: ROOM_PREFERENCE '{ROOM_PREFERENCE}' tidak valid. Gunakan 'free' atau 'paid'.")
        
    if not AGENT_NAME:
        raise ValueError("Error: AGENT_NAME tidak boleh kosong.")