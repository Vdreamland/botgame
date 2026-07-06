import asyncio
import json
import websockets
from src.config import WS_JOIN_URL, HEADERS, ROOM_PREFERENCE
from src.state_manager import StateManager

async def play_game(websocket):
    print("Starting gameplay loop...")
    manager = StateManager()
    try:
        async for message in websocket:
            data = json.loads(message)
            frame_type = data.get("type")
            
            if frame_type == "game_ended":
                print("\n========================================")
                print("Game has ended.")
                print("========================================\n")
                break
                
            manager.process_message(frame_type, data)
            
            if frame_type == "agent_view":
                if manager.is_agent_dead(data):
                    print("\n========================================")
                    print("Your agent has died. Terminating loop.")
                    print("========================================\n")
                    break
                
                pong_frame = {"type": "ping"}
                await websocket.send(json.dumps(pong_frame))
                
    except Exception as e:
        print(f"Error in gameplay loop: {e}")

async def run_ws_loop(active_game=None):
    if active_game:
        print(f"Active game found: {active_game.get('gameId')}. Resuming directly...")
    
    async with websockets.connect(WS_JOIN_URL, additional_headers=HEADERS) as websocket:
        print("Connected to WebSocket. Waiting for welcome frame...")
        
        welcome_msg = await websocket.recv()
        welcome_data = json.loads(welcome_msg)
        print(f"Welcome frame received. Decision: {welcome_data.get('decision')}")
        
        decision = welcome_data.get("decision")
        
        if decision == "BLOCKED":
            print("Access Blocked. Missing prerequisites:")
            print(json.dumps(welcome_data.get("readiness"), indent=2))
            return
            
        elif decision == "ALREADY_IN_GAME":
            print("Reconnected to running game.")
            await play_game(websocket)
            return
            
        elif decision in ["ASK_ENTRY_TYPE", "FREE_ONLY"]:
            hello_frame = {
                "type": "hello",
                "entryType": ROOM_PREFERENCE
            }
            await websocket.send(json.dumps(hello_frame))
            print(f"Sent hello frame with entryType: {ROOM_PREFERENCE}")
            
            async for message in websocket:
                msg_data = json.loads(message)
                msg_type = msg_data.get("type")
                
                if msg_type == "queued":
                    print("Enqueued in matchmaking. Waiting for assignment...")
                elif msg_type == "assigned":
                    print(f"Matched successfully! Game ID: {msg_data.get('gameId')}")
                    await play_game(websocket)
                    break
                elif msg_type == "not_selected":
                    print("Matchmaker cycle ended. Restarting...")
                    break
                elif msg_type == "error":
                    print(f"Connection error: {msg_data.get('code')} - {msg_data.get('message')}")
                    break