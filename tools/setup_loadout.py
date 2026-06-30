# tools/setup_loadout.py

import sys
import os
import asyncio
import aiohttp
from dotenv import load_dotenv

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from connection import ClawRoyaleHTTPClient, ClawRoyaleLoadoutClient
from ui import log_system

def calculate_relic_score(relic: dict) -> int:
    score = 0
    affixes = relic.get("affixes", [])
    if isinstance(affixes, list):
        for affix in affixes:
            if isinstance(affix, dict):
                stat = affix.get("statType")
                val = affix.get("rolledValue", 0)
                
                if stat == "hp_regen" and val < 0:
                    score -= 50 
                
                score += val
    return score

async def configure_bot(bot_name: str, api_key: str, version: str, http_client, loadout_client):
    try:
        relics_data = await loadout_client.get_relics_inventory(api_key, version)
        packs_data = await loadout_client.get_packs_inventory(api_key, version)

        relics = relics_data if isinstance(relics_data, list) else relics_data.get("relics", [])
        packs = packs_data if isinstance(packs_data, list) else packs_data.get("packs", [])

        log_system.success(f"[{bot_name}] Lobi inventory found: [{len(packs)} Packs] & [{len(relics)} Relics]")

        if len(packs) >= 1:
            main_pack = packs[0]
            main_id = main_pack.get("instanceId") or main_pack.get("id") or main_pack.get("instance_id") or main_pack.get("packInstanceId")
            
            log_system.success(f"[{bot_name}] Equipping Main Pack: {main_pack.get('displayName')}")
            await loadout_client.set_active_pack(api_key, version, main_id)

            if len(packs) >= 2:
                sub_pack = packs[1]
                sub_id = sub_pack.get("instanceId") or sub_pack.get("id") or sub_pack.get("instance_id") or sub_pack.get("packInstanceId")
                
                if sub_pack.get("category") != main_pack.get("category"):
                    log_system.success(f"[{bot_name}] Equipping Sub Pack: {sub_pack.get('displayName')}")
                    await loadout_client.set_sub_pack(api_key, version, sub_id)
                else:
                    log_system.warning(f"[{bot_name}] Sub Pack skipped: Must be a different category than Main Pack.")
        else:
            log_system.warning(f"[{bot_name}] No packs available to configure.")

        for slot_idx in [0, 1, 2]:
            matching_relics = [r for r in relics if r.get("typeIndex") == slot_idx]
            
            if matching_relics:
                matching_relics.sort(key=calculate_relic_score, reverse=True)
                best_relic = matching_relics[0]
                best_score = calculate_relic_score(best_relic)
                
                if best_score > 0:
                    relic_id = best_relic.get("instanceId") or best_relic.get("id") or best_relic.get("instance_id") or best_relic.get("relicInstanceId")
                    log_system.success(f"[{bot_name}] Equipping Best Relic {best_relic.get('baseName')} to Slot {slot_idx} (Quality Score: {best_score})")
                    await loadout_client.equip_relic(api_key, version, slot_idx, relic_id)
                else:
                    log_system.warning(f"[{bot_name}] Relic for Slot {slot_idx} skipped: Quality Score too low/unsafe ({best_score}).")
                    try:
                        await loadout_client.unequip_relic(api_key, version, slot_idx)
                        log_system.success(f"[{bot_name}] Slot {slot_idx} actively cleared.")
                    except Exception:
                        pass
            else:
                log_system.warning(f"[{bot_name}] No relics found in inventory for Slot {slot_idx}.")
                try:
                    await loadout_client.unequip_relic(api_key, version, slot_idx)
                    log_system.success(f"[{bot_name}] Slot {slot_idx} actively cleared.")
                except Exception:
                    pass

        final_loadout = await loadout_client.get_loadout(api_key, version)
        full_set = final_loadout.get("fullSet", False)

        if full_set:
            log_system.success(f"[{bot_name}] Loadout fullSet successfully activated!")
        else:
            log_system.warning(f"[{bot_name}] Loadout partial. Need 1 Main, 1 Sub, and 3 matched Relics for fullSet.")

    except Exception as e:
        log_system.error(f"[{bot_name}] Loadout operation failed: {str(e)}")

async def main():
    load_dotenv(dotenv_path=os.path.join(parent_dir, ".env"))
    num_bots = int(os.getenv("NUM_BOTS", "1"))

    async with aiohttp.ClientSession() as session:
        http_client = ClawRoyaleHTTPClient(session)
        loadout_client = ClawRoyaleLoadoutClient(session)

        try:
            version = await http_client.get_current_version()
            log_system.success(f"Active version detected: {version}")
        except Exception as e:
            log_system.error(f"Failed to fetch game version: {str(e)}")
            return

        log_system.success("Game database loaded successfully.")

        tasks = []
        for i in range(1, num_bots + 1):
            name = os.getenv(f"BOT{i}_NAME")
            key = os.getenv(f"BOT{i}_API_KEY")
            
            if name and key:
                tasks.append(configure_bot(name, key, version, http_client, loadout_client))
            else:
                log_system.warning(f"Configuration for BOT{i} is incomplete.")

        if tasks:
            await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log_system.info("Process stopped by user.")