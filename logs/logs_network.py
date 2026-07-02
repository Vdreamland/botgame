import json
from utils.logger import logger

def log_ws_connecting(bot_name: str, url: str):
    logger.info(f"[*] {bot_name} connecting to WebSocket -> {url}")

def log_ws_connected(bot_name: str):
    logger.info(f"[+] {bot_name} WebSocket connection established successfully.")

def log_ws_error(bot_name: str, error_msg: str):
    logger.error(f"{bot_name} WebSocket error: {error_msg}")

def log_ws_send(bot_name: str, data: dict):
    try:
        op_type = data.get("type") or data.get("op") or "unknown"
        logger.info(f"[»] {bot_name} sent {op_type} frame")
    except Exception:
        logger.info(f"[»] {bot_name} sent unknown frame")

def log_ws_receive(bot_name: str, data: str):
    try:
        obj = json.loads(data)
        msg_type = obj.get("type") or obj.get("op") or "unknown"
        if msg_type == "welcome":
            decision = obj.get("decision", "UNKNOWN")
            logger.info(f"[«] {bot_name} received welcome frame (Decision: {decision})")
        elif msg_type in ("queued", "assigned", "error"):
            logger.info(f"[«] {bot_name} received {msg_type} frame")
    except Exception:
        pass

def log_ws_closed(bot_name: str):
    logger.info(f"[-] {bot_name} WebSocket connection closed.")

def log_matchmaking_queued(bot_name: str):
    logger.info(f"[*] {bot_name} entered matchmaking queue.")

def log_match_assigned(bot_name: str):
    logger.info(f"[+] {bot_name} match assigned successfully. Ready for gameplay.")

def log_matchmaking_failed(bot_name: str, reason: str):
    logger.error(f"{bot_name} matchmaking failed: {reason}")

def log_ws_not_open_error(bot_name: str):
    logger.error(f"WebSocket error: {bot_name} connection is not open or has been disconnected.")

def log_missing_api_key():
    logger.error("API key is not configured in .env file.")

def log_connection_failed(bot_name: str):
    logger.error(f"{bot_name} failed to connect to the game server.")