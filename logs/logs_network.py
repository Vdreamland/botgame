import json
from utils.logger import logger

def log_ws_connecting(url: str):
    logger.info(f"\033[94m[*] Connecting to WebSocket -> {url}\033[0m")

def log_ws_connected():
    logger.info("\033[92m[+] WebSocket connection established successfully.\033[0m")

def log_ws_error(error_msg: str):
    logger.error(f"WebSocket error: {error_msg}")

def log_ws_send(data: dict):
    try:
        op_type = data.get("type") or data.get("op") or "unknown"
        logger.info(f"\033[96m[»] Sent {op_type} frame\033[0m")
    except Exception:
        logger.info("\033[96m[»] Sent unknown frame\033[0m")

def log_ws_receive(data: str):
    try:
        obj = json.loads(data)
        msg_type = obj.get("type") or obj.get("op") or "unknown"
        if msg_type == "welcome":
            decision = obj.get("decision", "UNKNOWN")
            logger.info(f"\033[93m[«] Received welcome frame (Decision: {decision})\033[0m")
        else:
            logger.info(f"\033[93m[«] Received {msg_type} frame\033[0m")
    except Exception:
        logger.info("\033[93m[«] Received unknown frame\033[0m")

def log_ws_closed():
    logger.info("\033[91m[-] WebSocket connection closed.\033[0m")