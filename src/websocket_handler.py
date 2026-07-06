import json
import websockets
from src.config import WS_JOIN_URL, HEADERS
from src.state_manager import StateManager
from src.ai import DecisionMaker

async def run_ws_loop(active_game=None, headers=None):
    use_headers = headers if headers else HEADERS
    if active_game:
        print(f"Active game found: {active_game.get('gameId')}. Resuming directly...")
    
    async with websockets.connect(WS_JOIN_URL, additional_headers=use_headers) as websocket:
        print("Connected to WebSocket. Waiting for welcome frame...")
        
        async for message in websocket:
            frame = json.loads(message)
            frame_type = frame.get("type")
            data = frame.get("data", {}) if "data" in frame else frame
            
            if frame_type == "welcome":
                decision = data.get("decision")
                print(f"Welcome frame received. Decision: {decision}")
                
                if decision == "ALREADY_IN_GAME":
                    print("Reconnected to running game.")
                    await play_game(websocket)
                    return
                elif decision in ["ASK_ENTRY_TYPE", "FREE_ONLY"]:
                    if decision == "ASK_ENTRY_TYPE":
                        entry_frame = {
                            "type": "hello",
                            "entryType": "free"
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
    manager.memory.reset_shared()
    manager.memory.reset_local()
    decision_maker = DecisionMaker()
    try:
        async for message in websocket:
            data = json.loads(message)
            frame_type = data.get("type")
            
            manager.process_message(frame_type, data)
            
            if manager.is_agent_dead():
                print("\n========================================")
                print("Your agent has died. Terminating loop.")
                print("========================================\n")
                break
                
            if frame_type in ["agent_view", "can_act_changed"]:
                if manager.can_act:
                    action = decision_maker.make_decision(manager, data)
                    manager.can_act = False
                    
                    from src.game_log import print_turn_log
                    print_turn_log(
                        manager.current_turn,
                        manager.status,
                        manager.zone_status,
                        manager.loot_status,
                        manager.radar_status,
                        manager.enemy_status,
                        manager.alive_count,
                        fight_history=manager.fight_history,
                        deadzone_status=manager.deadzone_status,
                        pending_loot_regions=manager.pending_loot_regions,
                        interacted_facilities=list(manager.interacted_facilities),
                        ai_decision=decision_maker.last_decision
                    )
                    
                    await websocket.send(json.dumps(action))
                    
            elif frame_type == "game_ended":
                print("\n========================================")
                print("Game has ended.")
                print("========================================\n")
                break
                
    except Exception as e:
        print(f"WebSocket connection error: {e}")