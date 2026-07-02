import os
import json
from dotenv import load_dotenv
from logs.quest_reward_log import (
    log_redeem_attempt,
    log_redeem_success,
    log_redeem_failed,
    log_weekly_check,
    log_weekly_claim_attempt,
    log_weekly_claim_success,
    log_weekly_claim_failed,
    log_no_claimable_weekly_tracks,
    log_weekly_tracks_failed,
    log_weekly_already_claimed
)

load_dotenv()

def get_configured_bots() -> list:
    num_bots = int(os.getenv("NUM_BOTS", 1))
    bots = []
    for i in range(1, num_bots + 1):
        name = os.getenv(f"BOT{i}_NAME")
        api_key = os.getenv(f"BOT{i}_API_KEY")
        if name and api_key:
            bots.append({"name": name, "api_key": api_key})
    return bots

def get_room_preference() -> str:
    return os.getenv("ROOM_PREFERENCE", "free")

async def auto_claim_rewards(api_client, bot_name: str):
    log_redeem_attempt(bot_name, "WELCOME")
    redeem_res = await api_client.redeem_code("WELCOME")
    if redeem_res.get("success"):
        log_redeem_success(bot_name, "WELCOME")
    else:
        error_raw = redeem_res.get("error")
        status = redeem_res.get("status")
        error_msg = f"status {status}"
        if error_raw:
            try:
                err_json = json.loads(error_raw)
                if isinstance(err_json, dict) and "error" in err_json:
                    sub_err = err_json["error"]
                    if isinstance(sub_err, dict):
                        code = sub_err.get("code")
                        msg = sub_err.get("message")
                        if code == "CONFLICT":
                            error_msg = "Code already redeemed by this account."
                        elif msg:
                            error_msg = msg
            except Exception:
                error_msg = error_raw
        log_redeem_failed(bot_name, "WELCOME", error_msg)

    log_weekly_check(bot_name)
    weekly_res = await api_client.get_weekly_tracks()
    if weekly_res.get("success"):
        data = weekly_res.get("data", {})
        is_claimed = data.get("claimed", False)
        if is_claimed:
            log_weekly_already_claimed(bot_name)
            return

        tracks = data.get("tracks", [])
        claimed_any = False
        for track in tracks:
            if isinstance(track, dict) and track.get("opened") is True:
                track_index = track.get("track")
                if track_index is not None:
                    log_weekly_claim_attempt(bot_name, track_index)
                    claim_res = await api_client.claim_weekly_reward(track_index)
                    if claim_res.get("success"):
                        log_weekly_claim_success(bot_name, track_index)
                        claimed_any = True
                        break
                    else:
                        claim_err = claim_res.get("error") or f"status {claim_res.get('status')}"
                        log_weekly_claim_failed(bot_name, track_index, claim_err)
        if not claimed_any:
            log_no_claimable_weekly_tracks(bot_name)
    else:
        log_weekly_tracks_failed(bot_name, weekly_res.get("error"))