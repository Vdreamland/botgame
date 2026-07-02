import asyncio
import os
from dotenv import load_dotenv
from utils.ws_client import ClawRoyaleWSClient
from utils.api_client import ClawRoyaleAPI
from logs.logs_network import (
    log_matchmaking_queued,
    log_match_assigned,
    log_matchmaking_failed,
    log_missing_api_key,
    log_connection_failed
)

load_dotenv()

async def test_connection():
    api_key = os.getenv("BOT1_API_KEY")
    if not api_key:
        log_missing_api_key()
        return

    room_preference = os.getenv("ROOM_PREFERENCE", "free")

    api_client = ClawRoyaleAPI(api_key=api_key)
    await api_client.auto_claim_rewards()

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
        log_connection_failed()

if __name__ == "__main__":
    asyncio.run(test_connection())