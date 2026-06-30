# tools/setup_loadout.py

import sys
import os
import asyncio
import aiohttp
from dotenv import load_dotenv

# Resolve and append parent directory to sys.path for connection and ui imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from connection import ClawRoyaleHTTPClient, ClawRoyaleLoadoutClient
from ui import log_system

def calculate_relic_score(relic: dict) -> int:
    """
    Calculates the quality score of a relic by summing up all its affix rolledValues.
    Positive affixes add to the score, negative ones reduce it.
    """
    score = 0
    affixes = relic.get("affixes", [])
    if isinstance(affixes, list):
        for affix in affixes:
            if isinstance(affix, dict):
                score += affix.get("rolledValue", 0)
    return score

async def main():
    load_dotenv(dotenv_path=os.path.join(parent_dir, ".env"))
    api_key = os.getenv("BOT1_API_KEY")
    
    if not api_key:
        log_system.error("BOT1_API_KEY is not configured in .env.")
        return

    async with aiohttp.ClientSession() as session:
        http_client = ClawRoyaleHTTPClient(session)
        loadout_client = ClawRoyaleLoadoutClient(session)

        # 1. Fetch current active game version
        try:
            version = await http_client.get_current_version()
            log_system.success(f"Active version detected: {version}")
        except Exception as e:
            log_system.error(f"Failed to fetch game version: {str(e)}")
            return

        log_system.success("Game database loaded successfully.")

        try:
            # 2. Fetch lobi inventory from API
            relics_data = await loadout_client.get_relics_inventory(api_key, version)
            packs_data = await loadout_client.get_packs_inventory(api_key, version)

            # Defensive parsing: Handle both raw list and wrapped dict responses safely
            relics = relics_data if isinstance(relics_data, list) else relics_data.get("relics", [])
            packs = packs_data if isinstance(packs_data, list) else packs_data.get("packs", [])

            log_system.success(f"Lobi inventory found: [{len(packs)} Packs] & [{len(relics)} Relics]")

            # 3. Equip Main Pack and Sub Pack (different category check)
            if len(packs) >= 1:
                main_pack = packs[0]
                main_id = main_pack.get("instanceId") or main_pack.get("id") or main_pack.get("instance_id") or main_pack.get("packInstanceId")
                
                log_system.success(f"Equipping Main Pack: {main_pack.get('displayName')}")
                await loadout_client.set_active_pack(api_key, version, main_id)

                if len(packs) >= 2:
                    sub_pack = packs[1]
                    sub_id = sub_pack.get("instanceId") or sub_pack.get("id") or sub_pack.get("instance_id") or sub_pack.get("packInstanceId")
                    
                    # Ensure sub pack has different category to avoid 409 conflict
                    if sub_pack.get("category") != main_pack.get("category"):
                        log_system.success(f"Equipping Sub Pack: {sub_pack.get('displayName')}")
                        await loadout_client.set_sub_pack(api_key, version, sub_id)
                    else:
                        log_system.warning("Sub Pack skipped: Must be a different category than Main Pack.")
            else:
                log_system.warning("No packs available to configure.")

            # 4. Filter, Sort by Score, and Equip Best Relics to Slots 0, 1, 2
            # Slots color mapping: 0=Red, 1=Green, 2=Blue
            for slot_idx in [0, 1, 2]:
                # Filter relics matching this specific slot color
                matching_relics = [r for r in relics if r.get("typeIndex") == slot_idx]
                
                if matching_relics:
                    # Sort relics by score descending (highest score first)
                    matching_relics.sort(key=calculate_relic_score, reverse=True)
                    best_relic = matching_relics[0]
                    relic_id = best_relic.get("instanceId") or best_relic.get("id") or best_relic.get("instance_id") or best_relic.get("relicInstanceId")
                    
                    if relic_id:
                        log_system.success(f"Equipping Best Relic {best_relic.get('baseName')} to Slot {slot_idx} (Quality Score: {calculate_relic_score(best_relic)})")
                        await loadout_client.equip_relic(api_key, version, slot_idx, relic_id)
                else:
                    log_system.warning(f"No relics found in inventory for Slot {slot_idx}.")

            # 5. Get final loadout status and verify fullSet active flag
            final_loadout = await loadout_client.get_loadout(api_key, version)
            full_set = final_loadout.get("fullSet", False)

            print()
            sys.stdout.flush()

            if full_set:
                log_system.success("Loadout fullSet successfully activated!")
            else:
                log_system.warning("Loadout partial. Need 1 Main, 1 Sub, and 3 matched Relics for fullSet.")

        except Exception as e:
            log_system.error(f"Loadout operation failed: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log_system.info("Process stopped by user.")