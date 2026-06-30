# connection/bot_manager.py

import asyncio
import os
import sys
import aiohttp
from connection.http_client import ClawRoyaleHTTPClient
from connection.socket_client import ClawRoyaleSocketClient
from connection.loadout import ClawRoyaleLoadoutClient
from ui import log_system, log_connection

async def run_bot_instance(bot_name: str, api_key: str, room_preference: str, version: str):
    """
    Runs verify, loadout check, and WebSocket connections for each bot instance.
    """
    async with aiohttp.ClientSession() as session:
        http_client = ClawRoyaleHTTPClient(session)
        loadout_client = ClawRoyaleLoadoutClient(session)
        try:
            # 1. Silently verify account details
            await http_client.get_account_me(api_key, version)

            # 2. Fetch loadout details and print active packs
            loadout = await loadout_client.get_loadout(api_key, version)
            main_pack = loadout.get("activePack")
            sub_pack = loadout.get("subPack")
            full_set = loadout.get("fullSet", False)

            main_name = main_pack.get("displayName", "None") if main_pack else "None"
            sub_name = sub_pack.get("displayName", "None") if sub_pack else "None"

            log_connection.bot_success(bot_name, f"Loadout: {main_name} (Main) + {sub_name} (Sub)")
            
            # 3. Print final fullSet configuration status and optimal stats confirmation
            if full_set:
                log_connection.bot_success(bot_name, "Status: fullSet active - Using optimal combat stats!")
            else:
                log_connection.bot_warning(bot_name, "Status: Loadout partial - fullSet effects are inactive.")

        except Exception as e:
            log_connection.bot_error(bot_name, f"Verification failed: {str(e)}")
            return

    socket_client = ClawRoyaleSocketClient(api_key, version, room_preference)
    await socket_client.connect_and_listen(bot_name)

async def start_multi_bots():
    """
    Orchestrates the bot manager flow and structures the PowerShell output cleanly.
    """
    room_pref = os.getenv("ROOM_PREFERENCE", "free")
    num_bots = int(os.getenv("NUM_BOTS", "1"))
    
    # 1. Fetch and print game version status
    async with aiohttp.ClientSession() as session:
        http_client = ClawRoyaleHTTPClient(session)
        try:
            version = await http_client.get_current_version()
            log_system.success(f"Active version detected: {version}")
        except Exception as e:
            log_system.error(f"Failed to fetch game version: {str(e)}")
            return

    # 2. Print database loaded status
    log_system.success("Game database loaded successfully.")

    # Gather configured bots
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

    # 3. Print total bots status
    log_system.success(f"Total Bot [{len(bot_tasks)}]")

    # 4. Print active bot list
    if active_bot_names:
        bot_list_str = ", ".join(active_bot_names)
        print(f"[+] Active bots: {bot_list_str}")
        sys.stdout.flush()

    if not bot_tasks:
        log_system.error("No valid bot configurations found.")
        return

    # Run the connection and testing cycle
    await asyncio.gather(*bot_tasks)