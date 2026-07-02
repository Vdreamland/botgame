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
        formatted = json.dumps(data)
        logger.info(f"\033[96m[»] Sent: {formatted}\033[0m")
    except Exception:
        logger.info(f"\033[96m[»] Sent: {data}\033[0m")

def log_ws_receive(data: str):
    try:
        obj = json.loads(data)
        formatted = json.dumps(obj)
        logger.info(f"\033[93m[«] Received: {formatted}\033[0m")
    except Exception:
        logger.info(f"\033[93m[«] Received: {data}\033[0m")

def log_ws_closed():
    logger.info("\033[91m[-] WebSocket connection closed.\033[0m")