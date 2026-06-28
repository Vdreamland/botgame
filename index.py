# -*- coding: utf-8 -*-
"""
ClawRoyale Index Entry Point.
Initializes system settings and boots the central orchestrator.
"""

import sys
import asyncio
from orchestrator import CentralOrchestrator

# Validasi kompatibilitas versi Python minimal (Python 3.8+ diperlukan untuk asyncio terintegrasi)
if sys.version_info < (3, 8):
    print("Fatal Error: Python 3.8 or higher is required to execute this asynchronus multi-agent.")
    sys.exit(1)


async def main():
    config_path = "config_agents.json"
    
    # Inisialisasi Koordinator Multi-Bot Utama
    orchestrator = CentralOrchestrator(config_path)
    
    try:
        # Jalankan eksekusi sistem secara asinkron
        await orchestrator.run_system()
    except KeyboardInterrupt:
        print("\nShutdown signal received (KeyboardInterrupt). Safely stopping bots...")
    finally:
        await orchestrator.shutdown_system()


if __name__ == "__main__":
    try:
        # Jalankan loop asinkron utama
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess closed safely by user. Goodbye!")