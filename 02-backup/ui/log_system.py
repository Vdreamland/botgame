# ui/log_system.py

import sys
from ui import GREEN, RED, RESET

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