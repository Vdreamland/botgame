import os
import json
from dotenv import load_dotenv

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

async def auto_claim_rewards(api_client, bot_name: str, bots_state: dict, draw_callback):
    bots_state[bot_name]["redeem"] = "Attempt"
    await draw_callback()

    redeem_res = await api_client.redeem_code("WELCOME")
    if redeem_res.get("success"):
        bots_state[bot_name]["redeem"] = "Success"
    else:
        error_raw = redeem_res.get("error")
        is_conflict = False
        if error_raw:
            try:
                err_json = json.loads(error_raw)
                if isinstance(err_json, dict) and "error" in err_json:
                    sub_err = err_json["error"]
                    if isinstance(sub_err, dict) and sub_err.get("code") == "CONFLICT":
                        is_conflict = True
            except Exception:
                pass
        if is_conflict:
            bots_state[bot_name]["redeem"] = "Already"
        else:
            bots_state[bot_name]["redeem"] = "Failed"
    await draw_callback()

    bots_state[bot_name]["weekly"] = "Checking"
    await draw_callback()

    weekly_res = await api_client.get_weekly_tracks()
    if weekly_res.get("success"):
        data = weekly_res.get("data", {})
        is_claimed = data.get("claimed", False)
        if is_claimed:
            bots_state[bot_name]["weekly"] = "Already"
            await draw_callback()
            return

        tracks = data.get("tracks", [])
        claimed_any = False
        for track in tracks:
            if isinstance(track, dict) and track.get("opened") is True:
                track_index = track.get("track")
                if track_index is not None:
                    claim_res = await api_client.claim_weekly_reward(track_index)
                    if claim_res.get("success"):
                        bots_state[bot_name]["weekly"] = "Claimed"
                        claimed_any = True
                        break
        if not claimed_any:
            bots_state[bot_name]["weekly"] = "No tracks"
    else:
        bots_state[bot_name]["weekly"] = "Failed"
    await draw_callback()