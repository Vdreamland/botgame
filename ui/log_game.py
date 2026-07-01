# ui/log_game.py

import sys
import aiohttp
from collections import Counter
from connection.loadout import ClawRoyaleLoadoutClient
from utility.detector.bot_stats_detector import detect_bot_stats
from utility.detector.inventory_detector import detect_inventory
from utility.detector.zone_detector import detect_zone

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

async def print_turn_log(bot_name: str, api_key: str, version: str, game_id: str, turn: int, self_data: dict, current_region: dict, view_data: dict, resolved_room_name: str = None) -> str:
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
    
    vision_range = self_data.get("vision", 1)
    
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
    print(f"Visibility [{vision_range}]")
    print(f"Location : {region_name} / Terrain : {terrain} / Weather : {weather} / Vision {vision} / Visibility Zone {visibility_zones} / Links {links_count}")
    print(f"Equipped : Weapon : {weapon_name} / Armor  : {armor_name}")
    print(f"Inventory ({inv['slot_count']}/10 Slots) : {inventory_str}")
    print()
    sys.stdout.flush()
    return room_name