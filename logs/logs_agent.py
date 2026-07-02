from utils.logger import logger

def log_orchestrator_start(num_bots: int):
    logger.info("[*] Detecting configured bots...")
    logger.info(f"[+] {num_bots} bots detected in configuration:")

def log_bots_list(names: list):
    names_str = " | ".join(names)
    logger.info(f"    - {names_str}")

def log_orchestrator_target(room_preference: str):
    logger.info(f"[*] Target room preference: {room_preference}")

def log_bot_lobby_wait(name: str):
    logger.info(f"[*] {name} waiting in lobby...")

def log_bot_lobby_ready():
    logger.info("[+] All bots ready in lobby. Initiating synchronized matchmaking queue.")

def log_bot_game_start(name: str):
    logger.info(f"[+] {name} connected to the game server.")

def log_bot_game_ended(name: str):
    logger.info(f"[-] {name} connection ended.")

def log_bot_waiting_cohort(name: str, active_count: int):
    logger.info(f"[*] {name} is waiting for other cohort bots to finish ({active_count} still in game)...")