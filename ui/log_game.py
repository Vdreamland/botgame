# ui/log_game.py

import sys
import asyncio
import aiohttp
from collections import Counter
from connection.loadout import ClawRoyaleLoadoutClient
from connection.http_client import ClawRoyaleHTTPClient
from utility.detector.bot_stats_detector import detect_bot_stats
from utility.detector.layer_detector import detect_layers
from ui.damage_logs import track_damage_event, get_turn_damage_reason
from ui.combat_logs import detect_combat_log_string
from ui.zone_logs import detect_zone_log_string
from ui.loot_logs import detect_loot_log_string
from ui import log_system, GREEN, RED, RESET
from utility.strategy.decision_engine import make_decision

async def print_turn_log(bot_name: str, api_key: str, version: str, game_id: str, turn: int, self_data: dict, current_region: dict, view_data: dict, joined_bots: list, resolved_room_name: str = None, log_state: dict = None) -> str:
    room_name = resolved_room_name
    balance = 0
    season_points = 0
    rank = "UNRANKED"
    
    async with aiohttp.ClientSession() as session:
        http_client = ClawRoyaleHTTPClient(session)
        
        if not room_name:
            room_name = await http_client.get_room_name(game_id, api_key, version)

        loadout_data = {}
        try:
            account_data = await http_client.get_account_me(api_key, version)
            balance = account_data.get("balance", 0)
            
            preseason_data = await http_client.get_preseason_summary(api_key, version)
            season_points = preseason_data.get("seasonPoints") or preseason_data.get("points") or 0
            rank = preseason_data.get("rank") or "UNRANKED"
        except Exception:
            pass

    stats = detect_bot_stats(self_data)
    hp = stats["hp"]
    max_hp = stats["max_hp"]
    is_alive = stats["is_alive"]

    # 1. Hitung Lapisan BFS Terlebih Dahulu
    layers = detect_layers(bot_name, self_data, current_region, view_data, joined_bots)

    # 2. Panggil Pembuat Log Modular Terpisah (Code Reuse & DRY) [2]
    combat_text = detect_combat_log_string(bot_name, self_data, layers)
    zone_text = detect_zone_log_string(current_region, view_data)
    loot_text = detect_loot_log_string(self_data)

    # 3. Panggil Log ZoneHistory khusus dari ui/damage_logs.py
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
    damage_text = f"ZoneHistory : {zone_history}"

    # 4. Satukan Seluruh Potongan Log Modular Menggunakan Baris Baru (Sangat Bersih & Terstruktur) [2]
    turn_log_text = (
        f"TURN {turn} [{bot_name}]\n"
        f"{combat_text}\n"
        f"{zone_text}\n"
        f"{loot_text}\n"
        f"{damage_text}"
    )

    # Kirim payload data lengkap beserta status preseason 1 ke server web lokal
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
                "season_points": season_points,
                "rank": rank,
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
        
        # Simpan memori jangka pendek wilayah kematian musuh untuk rute pergerakan taktis koin sMoltz (Loot)
        event_type = event_data.get("type")
        if event_type in ("agent_died", "death"):
            dead_r_id = event_data.get("regionId") or event_data.get("region_id")
            if dead_r_id:
                if "recent_kill_zones" not in log_state:
                    log_state["recent_kill_zones"] = []
                log_state["recent_kill_zones"].append(dead_r_id)
                if len(log_state["recent_kill_zones"]) > 5:
                    log_state["recent_kill_zones"].pop(0)
        return

    # Deteksi pesan akhir permainan (game_ended) secara resmi dari server game
    elif msg_type == "game_ended":
        if bot_name in client.joined_bots:
            client.joined_bots.remove(bot_name)
        log_system.success(f"[{bot_name}] Game ended. Disconnecting and ready to re-queue.")
        await ws.close()
        return

    if msg_type in ("assigned", "waiting"):
        if bot_name not in client.joined_bots:
            client.joined_bots.append(bot_name)
            print(f"[{bot_name}] successfully joined room!")
            sys.stdout.flush()

            # Pastikan pesan lobi "Game is ready" hanya dicetak sekali saat SEMUA bot sukses bergabung
            if len(client.joined_bots) == client.total_bots:
                print()  # Margin kosong
                print(f"{GREEN}[INFO]{RESET} Game is ready! Please open your browser at: http://localhost:8080")
                print()
                sys.stdout.flush()

    elif msg_type in ("agent_view", "turn_advanced", "action_result"):
        if not log_state.get("is_active_logged"):
            log_state["is_active_logged"] = True
            if bot_name not in client.joined_bots:
                client.joined_bots.append(bot_name)
                print(f"[{bot_name}] successfully joined room!")
                sys.stdout.flush()

                if len(client.joined_bots) == client.total_bots:
                    print()  # Margin kosong
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
            log_system.warning(f"[{bot_name}] Dead. Disconnecting and waiting to re-queue...")
            await ws.close()