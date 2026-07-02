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
            logger.info("[*] No claimable weekly reward tracks found.")
    else:
        logger.warning(f"[WARN] Failed to retrieve weekly tracks: {weekly_res.get('error')}")

    ws_client = ClawRoyaleWSClient(api_key=api_key)
    ws_url = "wss://cdn.clawroyale.ai/ws/join"
    
    success = await ws_client.connect(ws_url)
    if success:
        welcome_frame = await ws_client.receive()
        if welcome_frame and welcome_frame.get("type") == "welcome":
            decision = welcome_frame.get("decision")
            
            if decision in ("ASK_ENTRY_TYPE", "FREE_ONLY"):
                hello_payload = {
                    "type": "hello",
                    "entryType": room_preference,
                    "version": ws_client.api_version
                }
                await ws_client.send(hello_payload)
                
                while True:
                    frame = await ws_client.receive()
                    if frame is None:
                        break
                        
                    msg_type = frame.get("type")
                    if msg_type == "queued":
                        log_matchmaking_queued()
                    elif msg_type == "assigned":
                        log_match_assigned()
                        break
                    elif msg_type == "error":
                        error_msg = frame.get("message") or "Unknown error"
                        log_matchmaking_failed(error_msg)
                        break
            else:
                log_matchmaking_failed(f"Server decision: {decision}")
                
        await ws_client.close()
    else:
        logger.error("Failed to connect to the game server.")

if __name__ == "__main__":
    asyncio.run(test_connection())