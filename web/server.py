import os
import json
from aiohttp import web

async def handle_index(request):
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return web.Response(text=f.read(), content_type="text/html")

async def handle_status(request):
    bots_state = request.app["bots_state"]
    return web.json_response(bots_state)

async def handle_logs(request):
    bot_name = request.query.get("bot")
    if not bot_name:
        return web.Response(text="", content_type="text/plain")
    
    safe_name = os.path.basename(bot_name)
    log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "gameplay", f"{safe_name}.log")
    
    if not os.path.exists(log_path):
        return web.Response(text="", content_type="text/plain")
        
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/plain")
    except Exception:
        return web.Response(text="", content_type="text/plain")

async def start_web_server(bots_state: dict, host: str = "127.0.0.1", port: int = 8080):
    app = web.Application()
    app["bots_state"] = bots_state
    
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/status", handle_status)
    app.router.add_get("/api/logs", handle_logs)
    
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    app.router.add_static("/static/", static_dir)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()