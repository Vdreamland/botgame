# ui/log_system.py

import sys
import os

# ANSI escape codes for coloring
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

# Enable ANSI escape sequences support on Windows Console
if os.name == 'nt':
    import ctypes
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

def info(message: str):
    """Silent"""
    pass

def success(message: str):
    """Log system success with colored OK tag"""
    print(f"[+] {message} {GREEN}[OK]{RESET}")
    sys.stdout.flush()

def error(message: str):
    """Log system error with colored FAILED tag"""
    print(f"[-] {message} {RED}[FAILED]{RESET}")
    sys.stdout.flush()

def warning(message: str):
    """Log system warning with colored WARNING tag"""
    print(f"[!] {message} {RED}[WARNING]{RESET}")
    sys.stdout.flush()