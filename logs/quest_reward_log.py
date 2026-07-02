from utils.logger import logger

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

def log_no_claimable_weekly_tracks():
    logger.info("[*] No claimable weekly reward tracks found.")

def log_weekly_tracks_failed(reason: str):
    logger.warning(f"[WARN] Failed to retrieve weekly tracks: {reason}")