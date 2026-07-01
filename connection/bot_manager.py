# connection/bot_manager.py

import asyncio
import os
import sys
import aiohttp
from connection.http_client import ClawRoyaleHTTPClient
from connection.socket_client import ClawRoyaleSocketClient
from connection.loadout import ClawRoyaleLoadoutClient
from ui import log_system

async def run_bot_instance(bot_name: str, api_key: str, room_preference: str, version: str) -> dict:
    main_name = "None"
    sub_name = "None"
    full_set_status = "[No]"
    ws_status = "[FAILED]"

    async with aiohttp.ClientSession() as session:
        http_client = ClawRoyaleHTTPClient(session)
        loadout_client = ClawRoyaleLoadoutClient(session)
        try:
            await http_client.get_account_me(api_key, version)

            loadout = await loadout_client.get_loadout(api_key, version)
            main_pack = loadout.get("activePack")
            sub_pack = loadout.get("subPack")
            full_set = loadout.get("fullSet", False)

            main_name = main_pack.get("displayName", "None") if main_pack else "None"
            sub_name = sub_pack.get("displayName", "None") if sub_pack else "None"

            if full_set:
                full_set_status = "[OK]"
            else:
                full_set_status = "[No]"

        except Exception:
            full_set_status = "[No]"

        try:
            socket_client = ClawRoyaleSocketClient(api_key, version, room_preference)
            ws_success = await socket_client.connect_and_listen(bot_name, silent=True)
            if ws_success:
                ws_status = "[OK]"
            else:
                ws_status = "[FAILED]"
        except Exception:
            ws_status = "[FAILED]"

    return {
        "bot_name": bot_name,
        "loadout": f"{main_name} + {sub_name}",
        "full_set": full_set_status,
        "ws_test": ws_status
    }

async def start_multi_bots():
    room_pref = os.getenv("ROOM_PREFERENCE", "free")
    num_bots = int(os.getenv("NUM_BOTS", "1"))
    
    async with aiohttp.ClientSession() as session:
        http_client = ClawRoyaleHTTPClient(session)
        try:
            version = await http_client.get_current_version()
            log_system.success(f"Active version detected: {version}")
        except Exception as e:
            log_system.error(f"Failed to fetch game version: {str(e)}")
            return

    log_system.success("Game database loaded successfully.")

    bot_tasks = []
    active_bot_names = []
    for i in range(1, num_bots + 1):
        name = os.getenv(f"BOT{i}_NAME")
        key = os.getenv(f"BOT{i}_API_KEY")
        
        if name and key:
            bot_tasks.append(run_bot_instance(name, key, room_pref, version))
            active_bot_names.append(name)
        else:
            log_system.warning(f"Configuration for BOT{i} is incomplete.")

    log_system.success(f"Total Bot [{len(bot_tasks)}]")

    if not bot_tasks:
        log_system.error("No valid bot configurations found.")
        return

    results = await asyncio.gather(*bot_tasks)

    print()
    headers = f"{'BOT NAME':<13}  {'LOADOUT (MAIN + SUB)':<40}{'fullSet':<10}{'WS TEST'}"
    separator = "-" * len(headers)
    print(headers)
    print(separator)
    sys.stdout.flush()

    GREEN = "\033[92m"
    RED = "\033[91m"
    RESET = "\033[0m"

    for idx, res in enumerate(results, start=1):
        bot_name = res["bot_name"]
        loadout_str = res["loadout"]
        full_set_raw = res["full_set"]
        ws_test_raw = res["ws_test"]

        bot_idx_str = f"{idx}. {bot_name}"
        
        bot_idx_padded = f"{bot_idx_str:<13}  "
        loadout_padded = f"{loadout_str:<40}"
        full_set_padded = f"{full_set_raw:<10}"
        ws_test_padded = ws_test_raw

        full_set_colored = full_set_padded.replace("[OK]", f"{GREEN}[OK]{RESET}").replace("[No]", f"{RED}[No]{RESET}")
        ws_test_colored = ws_test_padded.replace("[OK]", f"{GREEN}[OK]{RESET}").replace("[FAILED]", f"{RED}[FAILED]{RESET}")

        print(f"{bot_idx_padded}{loadout_padded}{full_set_colored}{ws_test_colored}")
        sys.stdout.flush()

    joined_bots = []
    join_tasks = []
    for i in range(1, num_bots + 1):
        name = os.getenv(f"BOT{i}_NAME")
        key = os.getenv(f"BOT{i}_API_KEY")
        if name and key:
            client = ClawRoyaleSocketClient(key, version, room_pref, joined_bots, len(bot_tasks))
            join_tasks.append(client.connect_and_listen(name, silent=False))

    if join_tasks:
        print()
        await asyncio.gather(*join_tasks)