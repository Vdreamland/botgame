# ui/log_connection.py

import sys
from ui import GREEN, RED, RESET

def info(message: str):
    """Silent"""
    pass

def success(message: str):
    """Log general connection success with colored OK tag"""
    print(f"[+] {message} {GREEN}[OK]{RESET}")
    sys.stdout.flush()

def error(message: str):
    """Log general connection error with colored FAILED tag"""
    print(f"[-] {message} {RED}[FAILED]{RESET}")
    sys.stdout.flush()

def warning(message: str):
    """Log general connection warning with colored WARNING tag"""
    print(f"[!] {message} {RED}[WARNING]{RESET}")
    sys.stdout.flush()

def bot_info(bot_name: str, message: str):
    """Silent"""
    pass

def bot_success(bot_name: str, message: str):
    """Log bot success with colored OK tag at the end of the message"""
    print(f"[{bot_name}] {message} {GREEN}[OK]{RESET}")
    sys.stdout.flush()

def bot_error(bot_name: str, message: str):
    """Log bot connection error with colored FAILED tag"""
    print(f"[{bot_name}] {message} {RED}[FAILED]{RESET}")
    sys.stdout.flush()

def bot_warning(bot_name: str, message: str):
    """Log bot connection warning with colored WARNING tag"""
    print(f"[{bot_name}] {message} {RED}[WARNING]{RESET}")
    sys.stdout.flush()