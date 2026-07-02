from utils.logger import logger

def log_redeem_attempt(bot_name: str, code: str):
    logger.info(f"[*] {bot_name} attempting to redeem code: {code}")

def log_redeem_success(bot_name: str, code: str):
    logger.info(f"[+] {bot_name} successfully redeemed code: {code}")

def log_redeem_failed(bot_name: str, code: str, reason: str):
    logger.warning(f"{bot_name} failed to redeem code {code}: {reason}")

def log_weekly_check(bot_name: str):
    logger.info(f"[*] {bot_name} checking weekly reward tracks...")

def log_weekly_claim_attempt(bot_name: str, track_index: int):
    logger.info(f"[*] {bot_name} attempting to claim weekly reward track index: {track_index}")

def log_weekly_claim_success(bot_name: str, track_index: int):
    logger.info(f"[+] {bot_name} successfully claimed weekly reward track index: {track_index}")

def log_weekly_claim_failed(bot_name: str, track_index: int, reason: str):
    logger.warning(f"{bot_name} failed to claim weekly reward track index: {track_index} - {reason}")

def log_no_claimable_weekly_tracks(bot_name: str):
    logger.info(f"[*] {bot_name}: No claimable weekly reward tracks found.")

def log_weekly_tracks_failed(bot_name: str, reason: str):
    logger.warning(f"{bot_name} failed to retrieve weekly tracks: {reason}")

def log_weekly_already_claimed(bot_name: str):
    logger.info(f"[*] {bot_name}: Weekly rewards for this week have already been claimed.")