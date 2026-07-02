import asyncio
import os
from dotenv import load_dotenv
from utils.ws_client import ClawRoyaleWSClient
from utils.api_client import ClawRoyaleAPI
from utils.logger import logger
from logs.logs_network import (
    log_matchmaking_queued,
    log_match_assigned,
    log_matchmaking_failed
)
from logs.quest_reward_log import (
    log_redeem_attempt,
    log_redeem_success,
    log_redeem_failed,
    log_weekly_check,
    log_weekly_claim_attempt,
    log_weekly_claim_success,
    log_weekly_claim_failed
)

load_dotenv()

async def test_connection():
    api_key = os.getenv("BOT1_API_KEY")
    if not api_key:
        logger.error("API key is not configured in .env file.")
        return

    room_preference = os.getenv("ROOM_PREFERENCE", "free")

    api_client = ClawRoyaleAPI(api_key=api_key)

    log_redeem_attempt("WELCOME")
    redeem_res = await api_client.redeem_code("WELCOME")
    if redeem_res.get("success"):
        log_redeem_success("WELCOME")
    else:
        error_text = redeem_res.get("error") or f"status {redeem_res.get('status')}"
        log_redeem_failed("WELCOME", error_text)

    log_weekly_check()
    weekly_res = await api_client.get_weekly_tracks()
    if weekly_res.get("success"):
        data = weekly_res.get("data", {})
        tracks = data.get("tracks", [])
        claimed_any = False
        for track in tracks:
            if isinstance(track, dict) and track.get("opened") is True and track.get("claimed") is False:
                track_index = track.get("trackIndex")
                if track_index is not None:
                    log_weekly_claim_attempt(track_index)
                    claim_res = await api_client.claim_weekly_reward(track_index)
                    if claim_res.get("success"):
                        log_weekly_claim_success(track_index)
                        claimed_any = True
                        break
                    else:
                        claim_err = claim_res.get("error") or f"status {claim_res.get('status')}"
                        log_weekly_claim_failed(track_index, claim_err)
        if not claimed_any: