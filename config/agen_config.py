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
    profile_res = await api_client.get_my_profile()
    if profile_res.get("success"):
        data = profile_res.get("data", {})
        bots_state[bot_name]["smoltz"] = data.get("balance") if data.get("balance") is not None else data.get("sMoltz", 0)

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