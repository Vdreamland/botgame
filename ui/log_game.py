# ui/log_game.py

import sys
import asyncio
import aiohttp
from collections import Counter
from connection.loadout import ClawRoyaleLoadoutClient
from utility.detector.bot_stats_detector import detect_bot_stats
from utility.detector.inventory_detector import detect_inventory
from utility.detector.zone_detector import detect_zone
from utility.detector.layer_detector import detect_layers
from ui import log_system

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

async def fetch_room_name(game_id: str, api_key: str, version: str) -> str:
    url = f"https://cdn.clawroyale.ai/api/games/{game_id}"
    headers = {
        "X-API-Key": api_key,
        "X-Version": version
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as r:
                if r.status == 200:
                    res = await r.json()
                    if isinstance(res, dict) and res.get("success"):
                        data = res.get("data", {})
                        name = data.get("name") or data.get("title")
                        if name:
                            return name
    except Exception:
        pass
    return game_id[:8]

async def print_turn_log(bot_name: str, api_key: str, version: str, game_id: str, turn: int, self_data: dict, current_region: dict, view_data: dict, joined_bots: list, resolved_room_name: str = None) -> str:
    room_name = resolved_room_name
    if not room_name:
        room_name = await fetch_room_name(game_id, api_key, version)

    loadout_data = {}
    try:
        async with aiohttp.ClientSession() as session:
            loadout_client = ClawRoyaleLoadoutClient(session)
            loadout_data = await loadout_client.get_loadout(api_key, version)
    except Exception:
        pass

    stats = detect_bot_stats(self_data)
    inv = detect_inventory(self_data)
    zone = detect_zone(current_region, view_data)
    layers = detect_layers(bot_name, self_data, current_region, view_data, joined_bots)

    hp = stats["hp"]
    max_hp = stats["max_hp"]
    ep = stats["ep"]
    max_ep = stats["max_ep"]
    kills = stats["kills"]
    atk = stats["atk"]
    def_val = stats["def"]
    is_alive = stats["is_alive"]
    weapon_name = stats["weapon_name"]
    armor_name = stats["armor_name"]

    inventory_str = inv["items_str"]

    region_name = zone["region_name"]
    terrain = zone["terrain"]
    weather = zone["weather"]
    links_count = zone["links_count"]
    vision = zone["vision"]
    
    regions_list = view_data.get("visibleRegions") or view_data.get("regions")
    if isinstance(regions_list, list):
        visibility_zones = len(regions_list)
    else:
        visibility_zones = links_count + 1

    main_pack = loadout_data.get("activePack")
    sub_pack = loadout_data.get("subPack")
    main_name = main_pack.get("displayName") if main_pack else "None"
    sub_name = sub_pack.get("displayName") if sub_pack else "None"

    hp_color = RED if hp < (max_hp * 0.3) else GREEN
    hp_display = f"{hp_color}{hp}{RESET}"
    status_display = f"Status : {GREEN}ALIVE{RESET}" if is_alive else f"Status : {RED}DEAD{RESET}"

    print(f"# TURN {turn} [{bot_name}]")
    print(status_display)
    print(f"Hp {hp_display} / Ep {ep} / Kill {kills}")
    print(f"ATK: {atk} / DEF: {def_val}")
    print(f"Visibility [{visibility_zones}]")
    print(f"Location : {region_name} / Terrain : {terrain} / Weather : {weather} / Vision {vision} / Links {links_count}")
    
    for l_data in layers:
        print(f"Layer {l_data['layer']} : P {l_data['P']} / M {l_data['M']} / A {l_data['A']}")
        
    print(f"Equipped : Weapon : {weapon_name} / Armor  : {armor_name}")
    print(f"Inventory ({inv['slot_count']}/10 Slots) : {inventory_str}")
    print()
    sys.stdout.flush()
    return room_name

async def handle_message(client, bot_name: str, data: dict, ws):
    msg_type = data.get("type")
    log_state = client.log_state

    if msg_type in ("assigned", "waiting"):
        if bot_name not in client.joined_bots:
            client.joined_bots.append(bot_name)
            if len(client.joined_bots) == client.total_bots:
                print("All bots successfully joined room!")
                print()
                sys.stdout.flush()

    elif msg_type in ("agent_view", "turn_advanced", "action_result"):
        if not log_state.get("is_active_logged"):
            log_state["is_active_logged"] = True
            if bot_name not in client.joined_bots:
                client.joined_bots.append(bot_name)
                if len(client.joined_bots) == client.total_bots:
                    print("All bots successfully joined room!")
                    print()
                    sys.stdout.flush()

        view = data.get("view") or data.get("data", {}).get("view") or {}
        self_data = view.get("self", {})
        current_region = view.get("currentRegion", {})
        turn = data.get("turn") or view.get("turn") or 1
        
        is_alive = self_data.get("isAlive", True)
        if self_data.get("hp", 100) <= 0:
            is_alive = False

        if turn != log_state.get("last_printed_turn", -1):
            while len(client.joined_bots) < client.total_bots:
                await asyncio.sleep(0.5)

            game_id = data.get("gameId") or view.get("gameId") or ""
            resolved_name = log_state.get("resolved_room_name")
            if not resolved_name:
                resolved_name = await fetch_room_name(game_id, client.api_key, client.version)
                log_state["resolved_room_name"] = resolved_name

            if log_state.get("current_status") != "IN PROGRESS":
                log_state["current_status"] = "IN PROGRESS"

            await print_turn_log(
                bot_name=bot_name,
                api_key=client.api_key,
                version=client.version,
                game_id=game_id,
                turn=turn,
                self_data=self_data,
                current_region=current_region,
                view_data=view,
                joined_bots=client.joined_bots,
                resolved_room_name=resolved_name
            )
            log_state["last_printed_turn"] = turn

        if not is_alive:
            if bot_name in client.joined_bots:
                client.joined_bots.remove(bot_name)
            log_system.warning(f"[{bot_name}] Dead. Waiting for other bots to finish...")
            await ws.close()
            
            while len(client.joined_bots) > 0:
                await asyncio.sleep(1)
                
            await asyncio.sleep(30)
            log_state["is_dead_break"] = True