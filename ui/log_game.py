# ui/log_game.py

import sys
import asyncio
import aiohttp
from collections import Counter
from connection.loadout import ClawRoyaleLoadoutClient
from connection.http_client import ClawRoyaleHTTPClient
from utility.detector.bot_stats_detector import detect_bot_stats
from utility.detector.inventory_detector import detect_inventory
from utility.detector.zone_detector import detect_zone
from utility.detector.layer_detector import detect_layers
from ui.damage_logs import track_damage_event, get_turn_damage_reason
from ui import log_system, GREEN, RED, RESET

async def print_turn_log(bot_name: str, api_key: str, version: str, game_id: str, turn: int, self_data: dict, current_region: dict, view_data: dict, joined_bots: list, resolved_room_name: str = None, log_state: dict = None) -> str:
    room_name = resolved_room_name
    balance = 0
    
    async with aiohttp.ClientSession() as session:
        http_client = ClawRoyaleHTTPClient(session)
        
        if not room_name:
            room_name = await http_client.get_room_name(game_id, api_key, version)

        loadout_data = {}
        try:
            account_data = await http_client.get_account_me(api_key, version)
            balance = account_data.get("balance", 0)
            
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

    # Format representasi visual lapisan BFS menjadi satu baris horizontal terpisah pipa ( | )
    layers_parts = []
    for l_data in layers:
        layers_parts.append(f"Layer {l_data['layer']} : P {l_data['P']} / M {l_data['M']} / A {l_data['A']}")
    layers_block = " | ".join(layers_parts)

    # Status tampilan ALIVE / DEAD murni tanpa diganggu
    status_display_plain = "ALIVE" if is_alive else "DEAD"

    # Kalkulasi audit riwayat damage/healing per turn ke dalam baris ZoneHistory
    zone_history = "No damage events recorded."
    if log_state is not None:
        zone_history = get_turn_damage_reason(
            bot_name=bot_name,
            hp=hp,
            max_hp=max_hp,
            current_region=current_region,
            view_data=view_data,
            joined_bots=joined_bots,
            log_state=log_state
        )

    # Deteksi log peringatan ekspansi zona mati mendatang (Incoming Death Zone Warning)
    pending_dz = view_data.get("pendingDeathzones") or []
    if pending_dz:
        names = [rz.get("name") or rz.get("id") or "Unknown" for rz in pending_dz if isinstance(rz, dict)]
        dz_warning = f"Incoming ({', '.join(names)})"
    else:
        dz_warning = "None"

    # Deteksi semua wilayah yang sudah aktif menjadi zona mati (isDeathZone == True)
    active_dz_names = []
    if current_region.get("isDeathZone") or current_region.get("is_death_zone"):
        curr_name = current_region.get("name") or "Current Region"
        active_dz_names.append(curr_name)

    regions_to_check = view_data.get("visibleRegions") or view_data.get("regions") or []
    for rz in regions_to_check:
        if isinstance(rz, dict):
            if rz.get("isDeathZone") or rz.get("is_death_zone"):
                name = rz.get("name") or rz.get("id")
                if name and name not in active_dz_names:
                    active_dz_names.append(name)

    active_dz = ", ".join(active_dz_names) if active_dz_names else "None"

    # Susun ulang sesuai visual log format yang diminta, dengan tambahan ZoneHistory
    turn_log_text = (
        f"TURN {turn} [{bot_name}]\n"
        f"Status : {status_display_plain}\n"
        f"Hp {hp} / Ep {ep} / Kill {kills}\n"
        f"ATK: {atk} / DEF: {def_val}\n"
        f"Visibility [{visibility_zones}]\n"
        f"Location : {region_name} / Terrain : {terrain} / Weather : {weather} / Vision {vision} / Links {links_count}\n"
        f"Equipped : Weapon : {weapon_name} / Armor  : {armor_name}\n"
        f"Inventory ({inv['slot_count']}/10 Slots) : {inventory_str}\n"
        f"{layers_block}\n"
        f"ZoneHistory : {zone_history}\n"
        f"DeadZoneWarning : {dz_warning}\n"
        f"Active DeathZones : {active_dz}\n"
    )

    # Kirim payload data lengkap ke server web lokal
    async with aiohttp.ClientSession() as session:
        try:
            payload = {
                "bot_name": bot_name,
                "hp": hp,
                "max_hp": max_hp,
                "turn": turn,
                "is_alive": is_alive,
                "room_name": room_name,
                "balance": balance,
                "log_msg": turn_log_text
            }
            await session.post("http://localhost:8080/api/update", json=payload)
        except Exception:
            pass

    return room_name

async def handle_message(client, bot_name: str, data: dict, ws):
    msg_type = data.get("type")
    log_state = client.log_state

    # Tangkap real-time event frames untuk merekam pertempuran (damage/combat)
    if msg_type == "event":
        event_data = data.get("event") or {}
        track_damage_event(bot_name, event_data, log_state)
        return

    if msg_type in ("assigned", "waiting"):
        if bot_name not in client.joined_bots:
            client.joined_bots.append(bot_name)
            if len(client.joined_bots) == client.total_bots:
                print("All bots successfully joined room!")
                log_system.success("Web dashboard server started successfully.")
                print(f"{GREEN}[INFO]{RESET} Game is ready! Please open your browser at: http://localhost:8080")
                print()
                sys.stdout.flush()

    elif msg_type in ("agent_view", "turn_advanced", "action_result"):
        if not log_state.get("is_active_logged"):
            log_state["is_active_logged"] = True
            if bot_name not in client.joined_bots:
                client.joined_bots.append(bot_name)
                if len(client.joined_bots) == client.total_bots:
                    print("All bots successfully joined room!")
                    log_system.success("Web dashboard server started successfully.")
                    print(f"{GREEN}[INFO]{RESET} Game is ready! Please open your browser at: http://localhost:8080")
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
                async with aiohttp.ClientSession() as session:
                    http_client = ClawRoyaleHTTPClient(session)
                    resolved_name = await http_client.get_room_name(game_id, client.api_key, client.version)
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
                resolved_room_name=resolved_name,
                log_state=log_state
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