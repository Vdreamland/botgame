import os
import json
import queue
import asyncio
import threading
import logging
import mimetypes
from http import HTTPStatus
import websockets

logging.getLogger("websockets").setLevel(logging.CRITICAL)

PORT = int(os.environ.get("PORT", 8000))

CONNECTED_CLIENTS = set()
MESSAGE_QUEUE = queue.Queue()
BOTS_CACHE = {}

async def process_request(path, request_headers):
 try:
  is_ws = False
  
  try:
   for k in ["Upgrade", "upgrade"]:
    if k in request_headers:
     val = request_headers[k]
     if isinstance(val, bytes) and b"websocket" in val.lower():
      is_ws = True
     elif isinstance(val, str) and "websocket" in val.lower():
      is_ws = True
  except Exception:
   pass

  if not is_ws:
   try:
    headers_iterable = request_headers.items() if hasattr(request_headers, "items") else request_headers
    for k, v in headers_iterable:
     k_str = k.decode("utf-8", errors="ignore").lower() if isinstance(k, bytes) else str(k).lower()
     v_str = v.decode("utf-8", errors="ignore").lower() if isinstance(v, bytes) else str(v).lower()
     if k_str == "upgrade" and "websocket" in v_str:
      is_ws = True
      break
   except Exception:
    pass

  if is_ws:
   return None

  if path == "/":
   file_name = "index.html"
  else:
   file_name = path.lstrip("/")

  base_dir = os.path.dirname(os.path.abspath(__file__))
  file_path = os.path.join(base_dir, file_name)

  real_base = os.path.realpath(base_dir)
  real_file = os.path.realpath(file_path)
  if not real_file.startswith(real_base):
   return 403, [("Content-Type", "text/plain")], b"Forbidden"

  if os.path.exists(file_path) and os.path.isfile(file_path):
   content_type, _ = mimetypes.guess_type(file_path)
   if not content_type:
    content_type = "application/octet-stream"
   
   with open(file_path, "rb") as f:
    body = f.read()
   
   headers = [
    ("Content-Type", content_type),
    ("Content-Length", str(len(body))),
   ]
   return 200, headers, body

  return 404, [("Content-Type", "text/plain")], b"Not Found"

 except Exception as e:
  print(f"Error in process_request: {e}")
  return 500, [("Content-Type", "text/plain")], f"Internal Server Error: {e}".encode()

async def ws_handler(websocket):
 CONNECTED_CLIENTS.add(websocket)
 try:
  if BOTS_CACHE:
   for bot_name, data in BOTS_CACHE.items():
    if data:
     initial_payload = {
      "type": "state_update",
      "bot_name": bot_name,
      "data": data
     }
     await websocket.send(json.dumps(initial_payload))
  
  async for message in websocket:
   pass
 except websockets.exceptions.ConnectionClosed:
  pass
 finally:
  CONNECTED_CLIENTS.remove(websocket)

async def run_ws_server():
 async with websockets.serve(ws_handler, "0.0.0.0", PORT, process_request=process_request):
  while True:
   await asyncio.sleep(0.1)
   try:
    while not MESSAGE_QUEUE.empty():
     msg = MESSAGE_QUEUE.get_nowait()
     payload = json.dumps(msg)
     if CONNECTED_CLIENTS:
      await asyncio.gather(*[client.send(payload) for client in CONNECTED_CLIENTS], return_exceptions=True)
   except Exception:
    pass

def run_ws_loop():
 asyncio.run(run_ws_server())

def start_server():
 ws_thread = threading.Thread(target=run_ws_loop, daemon=True)
 ws_thread.start()

def broadcast(message_dict):
 bot_name = message_dict.get("bot_name")
 if not bot_name:
  return

 if message_dict["type"] == "state_update":
  BOTS_CACHE[bot_name] = message_dict["data"]

 MESSAGE_QUEUE.put(message_dict)