# ui/web/server.py
import os
import asyncio
from aiohttp import web

BOTS_DATA = {}
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

def extract_template_block(block_name: str) -> str:
    try:
        index_path = os.path.join(TEMPLATE_DIR, "index.html")
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        start_tag = f'<template id="{block_name}">'
        end_tag = "</template>"
        
        start_idx = content.find(start_tag)
        if start_idx != -1:
            end_idx = content.find(end_tag, start_idx)
            if end_idx != -1:
                return content[start_idx + len(start_tag):end_idx].strip()
    except Exception:
        pass
    return ""

async def index_handler(request):
    try:
        with open(os.path.join(TEMPLATE_DIR, "index.html"), "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html")
    except FileNotFoundError:
        return web.Response(text="index.html not found.", status=404)

async def css_handler(request):
    try:
        with open(os.path.join(TEMPLATE_DIR, "style.css"), "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/css")
    except FileNotFoundError:
        return web.Response(text="style.css not found.", status=404)

async def update_handler(request):
    try:
        data = await request.json()
        bot_name = data.get("bot_name")
        if not bot_name:
            return web.json_response({"success": False, "error": "Missing bot_name"}, status=400)
        
        if bot_name not in BOTS_DATA:
            BOTS_DATA[bot_name] = {
                "name": bot_name,
                "hp": 100,
                "max_hp": 100,
                "turn": 1,
                "is_alive": True,
                "room_name": "Unknown",
                "balance": 0,
                "logs": []
            }
        
        BOTS_DATA[bot_name].update({
            "hp": data.get("hp", BOTS_DATA[bot_name]["hp"]),
            "max_hp": data.get("max_hp", BOTS_DATA[bot_name]["max_hp"]),
            "turn": data.get("turn", BOTS_DATA[bot_name]["turn"]),
            "is_alive": data.get("is_alive", BOTS_DATA[bot_name]["is_alive"]),
            "room_name": data.get("room_name", BOTS_DATA[bot_name]["room_name"]),
            "balance": data.get("balance", BOTS_DATA[bot_name]["balance"]),
        })

        log_msg = data.get("log_msg")
        if log_msg:
            BOTS_DATA[bot_name]["logs"].append(log_msg)
            if len(BOTS_DATA[bot_name]["logs"]) > 300:
                BOTS_DATA[bot_name]["logs"].pop(0)

        return web.json_response({"success": True})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def bots_list_handler(request):
    if not BOTS_DATA:
        return web.Response(text='<div class="no-bots">Waiting for bots to join...</div>', content_type="text/html")
    
    selected_bot = request.query.get("selected")
    template = extract_template_block("BOT_ITEM")
    if not template:
        return web.Response(text="Template BOT_ITEM not found.", status=500)
    
    html_parts = []
    for name, bot in sorted(BOTS_DATA.items()):
        status_text = "ALIVE" if bot["is_alive"] else "DEAD"
        active_class = "active-bot" if selected_bot == name else ""
        
        btn_html = template.format(
            name=name,
            status_text=status_text,
            active_class=active_class,
            hp=bot["hp"],
            max_hp=bot["max_hp"],
            turn=bot["turn"],
            room_name=bot.get("room_name", "Unknown"),
            balance=bot.get("balance", 0)
        )
        html_parts.append(btn_html)
    
    total_smoltz = sum(bot.get("balance", 0) for bot in BOTS_DATA.values())
    total_widget_html = f'<div class="total-smoltz-card">Total sMoltz: <span>{total_smoltz}</span></div>'
    
    full_sidebar_html = total_widget_html + "\n" + "\n".join(html_parts)
    return web.Response(text=full_sidebar_html, content_type="text/html")

async def bot_detail_handler(request):
    bot_name = request.match_info.get("bot_name")
    bot = BOTS_DATA.get(bot_name)
    if not bot:
        return web.Response(text='<div class="no-selection">Silakan pilih bot di sebelah kiri untuk memantau status.</div>', content_type="text/html")
    
    # Ambil parameter query penanda pembanding polling (HTTP 204 Optimization)
    current_turn_req = request.query.get("current_turn")
    log_count_req = request.query.get("log_count")
    
    if current_turn_req is not None and log_count_req is not None:
        try:
            if int(current_turn_req) == bot["turn"] and int(log_count_req) == len(bot["logs"]):
                # Kembalikan HTTP 204 No Content untuk menghentikan pembaruan DOM (posisi scroll terjaga sempurna)
                return web.Response(status=204)
        except ValueError:
            pass

    template = extract_template_block("BOT_DETAIL")
    if not template:
        return web.Response(text="Template BOT_DETAIL not found.", status=500)

    logs_str = "\n".join(bot["logs"]) if bot["logs"] else "Waiting for turn actions..."
    log_count = len(bot["logs"])

    detail_html = template.format(
        name=bot["name"],
        turn=bot["turn"],
        room_name=bot.get("room_name", "Unknown"),
        logs_str=logs_str,
        log_count=log_count
    )
    
    return web.Response(text=detail_html, content_type="text/html")

server_runner = None

async def start_dashboard_server(host: str = "localhost", port: int = 8080):
    app = web.Application()
    
    app.router.add_get("/", index_handler)
    app.router.add_get("/templates/style.css", css_handler)
    app.router.add_get("/style.css", css_handler)
    app.router.add_post("/api/update", update_handler)
    app.router.add_get("/api/bots", bots_list_handler)
    app.router.add_get("/api/bot/{bot_name}", bot_detail_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    global server_runner
    server_runner = runner
    
    os.makedirs(TEMPLATE_DIR, exist_ok=True)

async def stop_dashboard_server():
    global server_runner
    if server_runner:
        await server_runner.cleanup()