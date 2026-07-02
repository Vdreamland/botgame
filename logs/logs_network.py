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