import json
import websockets
from src.config import WS_JOIN_URL, HEADERS
from src.state_manager import StateManager
from src.ai import DecisionMaker

async def run_ws_loop(active_game=None):
    if active_game:
        print(f"Active game found: {active_game.get('gameId')}. Resuming directly...")
        
    async with websockets.connect(WS_JOIN_URL, additional_headers=HEADERS) as websocket:
        hello_frame = {
            "type": "hello",
            "data": {
                "entryType": "free"
            }
        }
        await websocket.send(json.dumps(hello_frame))
        print("Connected to WebSocket. Waiting for welcome frame...")
        
        async for message in websocket:
            frame = json.loads(message)
            frame_type = frame.get("type")
            data = frame.get("data", {}) if "data" in frame else frame.get("view", {})
            decision = data.get("decision") if isinstance(data, dict) else None
            
            if frame_type == "welcome":
                decision_val = data.get("decision")
                print(f"Welcome frame received. Decision: {decision_val}")
                
                if decision_val == "ALREADY_IN_GAME":
                    print("Reconnected to running game.")
                    await play_game(websocket)
                    return
                elif decision_val in ["ASK_ENTRY_TYPE", "FREE_ONLY"]:
                    if decision_val == "ASK_ENTRY_TYPE":
                        entry_frame = {
                            "type": "entry_type",
                            "data": {
                                "entryType": "free"
                            }
                        }
                        await websocket.send(json.dumps(entry_frame))
                        print("Sent hello frame with entryType: free")
                    print("Enqueued in matchmaking. Waiting for assignment...")
                    
            elif frame_type == "assigned":
                print(f"Matched successfully! Game ID: {data.get('gameId')}")
                await play_game(websocket)
                break

async def play_game(websocket):
    print("Starting gameplay loop...")
    manager = StateManager()
    decision_maker = DecisionMaker()
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
            
            if manager.is_agent_dead():
                print("\n========================================")
                print("Your agent has died. Terminating loop.")
                print("========================================\n")
                break
                
            if frame_type == "agent_view":
                action = decision_maker.make_decision(manager, data)
                action_type = action.get("data", {}).get("actionType", "Unknown")
                print(f"Decision: {action_type}")
                await websocket.send(json.dumps(action))
    except Exception as e:
        print(f"WebSocket connection error: {e}")