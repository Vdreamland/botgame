import os
import json
import queue
import asyncio
import threading
import logging
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import websockets

logging.getLogger("websockets").setLevel(logging.CRITICAL)

HTTP_PORT = 8000
WS_PORT = 8765

CONNECTED_CLIENTS = set()
MESSAGE_QUEUE = queue.Queue()
BOTS_CACHE = {}

class WebDashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        directory = os.path.dirname(os.path.abspath(__file__))
        super().__init__(*args, directory=directory, **kwargs)

    def log_message(self, format, *args):
        pass

def run_http_server():
    server = ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), WebDashboardHandler)
    server.serve_forever()

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
    async with websockets.serve(ws_handler, "0.0.0.0", WS_PORT):
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
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    ws_thread = threading.Thread(target=run_ws_loop, daemon=True)
    ws_thread.start()

def broadcast(message_dict):
    bot_name = message_dict.get("bot_name")
    if not bot_name:
        return

    if message_dict["type"] == "state_update":
        BOTS_CACHE[bot_name] = message_dict["data"]

    MESSAGE_QUEUE.put(message_dict)