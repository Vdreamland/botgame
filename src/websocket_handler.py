import json
import websockets
from src.config import WS_JOIN_URL, HEADERS, ROOM_PREFERENCE
from src.state_manager import StateManager
from src.ai import DecisionMaker

async def run_ws_loop(active_game=None, headers=None):
 use_headers = headers if headers else HEADERS
 active_game_id = active_game.get("gameId") if active_game else None
 if active_game_id:
  print(f"Active game found: {active_game_id}. Resuming directly...")
  
 async with websockets.connect(WS_JOIN_URL, additional_headers=use_headers) as websocket:
  print("Connected to WebSocket. Waiting for welcome frame...")
  async for message in websocket:
   frame = json.loads(message)
   frame_type = frame.get("type")
   data = frame.get("data", {}) if "data" in frame else frame
   
   if frame_type == "welcome":
    decision = data.get("decision")
    print(f"Welcome frame received. Decision: {decision}")
    if decision == "ALREADY_IN_GAME" and active_game_id:
     print("Reconnected to running game.")
     res = await play_game(websocket, active_game_id, is_reconnect=True)
     return res, active_game_id
    elif decision in ["ASK_ENTRY_TYPE", "FREE_ONLY"]:
     if decision == "ASK_ENTRY_TYPE":
      entry_frame = {
       "type": "hello",
       "entryType": ROOM_PREFERENCE
      }
      await websocket.send(json.dumps(entry_frame))
      print(f"Sent hello frame with entryType: {ROOM_PREFERENCE}")
      print("Enqueued in matchmaking. Waiting for assignment...")
   elif frame_type == "assigned":
    assigned_game_id = data.get("gameId")
    print(f"Matched successfully! Game ID: {assigned_game_id}")
    res = await play_game(websocket, assigned_game_id, is_reconnect=False)
    return res, assigned_game_id
  return True, active_game_id

async def play_game(websocket, game_id, is_reconnect=False):
 print("Starting gameplay loop...")
 manager = StateManager()
 manager.game_id = game_id
 manager.memory.set_shared_file(f"shared_team_memory_{game_id}.json")
 if not is_reconnect:
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
    return False
   
   trigger_decision = False
   decision_data = data
   
   if "view" in data:
    if manager.can_act:
     trigger_decision = True
   elif frame_type == "can_act_changed" and manager.can_act and manager.last_view:
    trigger_decision = True
    decision_data = {
     "type": "agent_view",
     "view": manager.last_view,
     "turn": manager.current_turn
    }
   
   if trigger_decision:
    from src.ai.strategy.whisper_sabotage import generate_sabotage_whispers
    whisper_actions = generate_sabotage_whispers(manager, decision_data)
    for whisper in whisper_actions:
     await websocket.send(json.dumps(whisper))
    
    action = decision_maker.make_decision(manager, decision_data)
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
     ai_decision=decision_maker.last_decision,
     game_id=game_id
    )
    await websocket.send(json.dumps(action))
   elif frame_type == "game_ended":
    print("\n========================================")
    print("Game has ended.")
    print("========================================\n")
    return True
  return True
 except Exception as e:
  print(f"WebSocket connection error: {e}")
  raise e
 finally:
  manager.memory.cleanup_shared()