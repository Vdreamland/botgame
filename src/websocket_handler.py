import asyncio
import json
import websockets
from src.config import WS_JOIN_URL, HEADERS, ROOM_PREFERENCE
from src.game_log import print_turn_log
from src.ai.detector.self_detector import parse_self_status

async def play_game(websocket):
    print("Starting gameplay loop...")
    
    current_turn = 1
    alive_count = 0
    status = {
        "name": "Unknown",
        "hp": 0,
        "max_hp": 0,
        "ep": 0,
        "max_ep": 0,
        "is_alive": True,
        "region_id": None,
        "has_weapon": False,
        "equipped_weapon": None,
        "has_armor": False,
        "equipped_armor": None,
        "inventory_count": 0,
        "inventory_free_slots": 10
    }
    
    try:
        async for message in websocket:
            data = json.loads(message)
            frame_type = data.get("type")
            
            if frame_type == "game_ended":
                print("\n========================================")
                print("Game has ended.")
                print("========================================\n")
                break
                
            elif frame_type == "agent_view":
                view_data = data.get("view", {})
                status = parse_self_status(data)
                
                current_turn = data.get("turn", current_turn)
                alive_count = view_data.get("aliveCount", alive_count)
                
                print_turn_log(current_turn, status, alive_count)
                
                if status["hp"] == 0 or not status["is_alive"]:
                    print("\n========================================")
                    print("Your agent has died. Terminating loop.")
                    print("========================================\n")
                    break
                
                pong_frame = {"type": "ping"}
                await websocket.send(json.dumps(pong_frame))
                
            elif frame_type == "turn_advanced":
                current_turn = data.get("turn", current_turn + 1)
                alive_count = data.get("aliveCount", alive_count)
                
                print_turn_log(current_turn, status, alive_count)
                
            elif frame_type == "hp_changed":
                new_hp = data.get("hp", data.get("currentHp", status.get("hp", 0)))
                status["hp"] = new_hp
                if new_hp == 0:
                    status["is_alive"] = False
                    
            elif frame_type == "ep_changed":
                new_ep = data.get("ep", data.get("currentEp", status.get("ep", 0)))
                status["ep"] = new_ep
                
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