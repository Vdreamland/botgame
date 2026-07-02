import json
from utils.logger import logger

def log_ws_connecting(url: str):
    logger.info(f"[*] Connecting to WebSocket -> {url}")

def log_ws_connected():
    logger.info("[+] WebSocket connection established successfully.")

def log_ws_error(error_msg: str):
    logger.error(f"WebSocket error: {error_msg}")

def log_ws_send(data: dict):
    try:
        op_type = data.get("type") or data.get("op") or "unknown"
        logger.info(f"[»] Sent {op_type} frame")
    except Exception:
        logger.info("[»] Sent unknown frame")

def log_ws_receive(data: str):
    try:
        obj = json.loads(data)
        msg_type = obj.get("type") or obj.get("op") or "unknown"
        if msg_type == "welcome":
            decision = obj.get("decision", "UNKNOWN")
            logger.info(f"[«] Received welcome frame (Decision: {decision})")
        else:
            logger.info(f"[«] Received {msg_type} frame")
    except Exception:
        logger.info("[«] Received unknown frame")

def log_ws_closed():
    logger.info("[-] WebSocket connection closed.")

def log_matchmaking_queued():
    logger.info("[*] Bot entered matchmaking queue.")

def log_match_assigned():
    logger.info("[+] Match assigned successfully. Ready for gameplay.")

def log_matchmaking_failed(reason: str):
    logger.error(f"Matchmaking failed: {reason}")

def log_ws_not_open_error():
    logger.error("WebSocket error: WebSocket connection is not open or has been disconnected.")

def log_missing_api_key():
    logger.error("API key is not configured in .env file.")

def log_connection_failed():
    logger.error("Failed to connect to the game server.")