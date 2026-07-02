import os
import asyncio
from aiohttp import web

async def handle_status(request):
    bots_state = request.app["bots_state"]
    return web.json_response(bots_state)

async def handle_index(request):
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(template_path, "r") as f:
        html = f.read()
    return web.Response(text=html, content_type="text/html")

async def start_web_server(bots_state: dict, host: str = "127.0.0.1", port: int = 8080):
    app = web.Application()
    app["bots_state"] = bots_state
    
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/status", handle_status)
    
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    app.router.add_static("/static/", path=static_dir, name="static")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    while True:
        await asyncio.sleep(3600)