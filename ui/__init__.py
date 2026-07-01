# ui/__init__.py

import os

# Konstanta warna ANSI global
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

# Aktifkan dukungan warna ANSI di Windows Console secara otomatis saat modul ui dimuat
if os.name == 'nt':
    import ctypes
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

from . import log_system
from . import log_connection