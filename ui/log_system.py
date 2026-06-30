# ui/log_system.py

import sys
import os

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

if os.name == 'nt':
    import ctypes
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

def info(message: str):
    pass

def success(message: str):
    print(f"{GREEN}[OK]{RESET} {message}")
    sys.stdout.flush()

def error(message: str):
    print(f"{RED}[FAILED]{RESET} {message}")
    sys.stdout.flush()

def warning(message: str):
    print(f"{RED}[WARNING]{RESET} {message}")
    sys.stdout.flush()