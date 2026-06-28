# -*- coding: utf-8 -*-
"""
ClawRoyale Index Entry Point.
Initializes system settings and boots the central orchestrator.
"""

import os
import sys
import shutil
import asyncio
from orchestrator import CentralOrchestrator

# Validasi kompatibilitas versi Python minimal (Python 3.8+ diperlukan untuk asyncio terintegrasi)
if sys.version_info < (3, 8):
    print("Fatal Error: Python 3.8 or higher is required to execute this asynchronus multi-agent.")
    sys.exit(1)


def clear_startup_logs():
    """
    Clears all old log files inside /logs directory at start, keeping the folder itself.
    """
    log_dir = "logs"
    if os.path.exists(log_dir):
        for filename in os.listdir(log_dir):
            file_path = os.path.join(log_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception:
                pass


async def main():
    config_path = "config_agents.json"
    
    # Inisialisasi Koordinator Multi-Bot Utama
    orchestrator = CentralOrchestrator(config_path)
    
    try:
        # Jalankan eksekusi sistem secara asinkron
        await orchestrator.run_system()
    except KeyboardInterrupt:
        print("\nShutdown signal received (KeyboardInterrupt). Safely stopping bots...")


if __name__ == "__main__":
    # Bersihkan seluruh berkas log usang di folder logs/ sesaat sebelum program booting
    clear_startup_logs()
    
    try:
        # Jalankan loop asinkron utama
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess closed safely by user. Goodbye!")