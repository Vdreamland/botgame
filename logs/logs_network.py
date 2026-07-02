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

def log_redeem_attempt(code: str):
    logger.info(f"[*] Attempting to redeem code: {code}")

def log_redeem_success(code: str):
    logger.info(f"[+] Successfully redeemed code: {code}")

def log_redeem_failed(code: str, reason: str):
    logger.warning(f"[WARN] Failed to redeem code {code}: {reason}")

def log_weekly_check():
    logger.info("[*] Checking weekly reward tracks...")

def log_weekly_claim_attempt(track_index: int):
    logger.info(f"[*] Attempting to claim weekly reward track index: {track_index}")

def log_weekly_claim_success(track_index: int):
    logger.info(f"[+] Successfully claimed weekly reward track index: {track_index}")

def log_weekly_claim_failed(track_index: int, reason: str):
    logger.warning(f"[WARN] Failed to claim weekly reward track index: {track_index} - {reason}")