import os
import asyncio
import sys
from config import settings
from src.websocket.lobby.join_handler import JoinHandler
from src.websocket.battle.agent_handler import AgentHandler
from src.utils.logger import logger

async def auto_equip_lobby(api_key: str, bot_name: str):
    """Automatically optimize and equip the best available lobby loadout."""
    logger.info(f"[{bot_name}] Evaluating lobby inventory for loadout optimization...")
    from src.api.loadout import LobbyLoadoutManager
    manager = LobbyLoadoutManager(api_key)
    
    # 1. OPTIMIZE ACTIVE PACK (T1 > T2 > T3)
    packs = await manager.get_packs_inventory()
    if isinstance(packs, list) and len(packs) > 0:
        # Maps integer and string tiers to dynamic weights (1 or T1 is highest weight)
        tier_weights = {1: 3, 2: 2, 3: 1, "T1": 3, "T2": 2, "T3": 1}
        # Sort descending by tier weight safely
        packs.sort(key=lambda p: tier_weights.get(p.get("tier", 3), 0) if isinstance(p, dict) else 0, reverse=True)
        best_pack = packs[0]
        best_pack_id = best_pack.get("id") if isinstance(best_pack, dict) else None
        
        loadout = await manager.get_loadout()
        current_pack = loadout.get("activePack", {})
        current_pack_id = current_pack.get("id") if isinstance(current_pack, dict) else None
        
        if best_pack_id and best_pack_id != current_pack_id:
            logger.info(f"[{bot_name}] Equipping stronger active pack...")
            await manager.equip_pack(best_pack_id)

    # 2. OPTIMIZE RELICS
    relics = await manager.get_relics_inventory()
    if isinstance(relics, list) and len(relics) > 0:
        slots_to_check = [0, 1, 2]
        for slot_index in slots_to_check:
            # Use safe for-loop append instead of list comprehension to prevent indexing bugs
            slot_relics = []
            for r in relics:
                if isinstance(r, dict):
                    t_idx = r.get("typeIndex")
                    if t_idx == slot_index:
                        slot_relics.append(r)
                        
            if len(slot_relics) == 0:
                continue
                
            # Score each relic based on cumulative positive/negative affix values
            scored_relics = []
            for relic in slot_relics:
                score = 0
                affixes = relic.get("affixes", [])
                if isinstance(affixes, list):
                    for affix in affixes:
                        if isinstance(affix, dict):
                            val = affix.get("rolledValue") or affix.get("value") or 0
                            score += val
                scored_relics.append((score, relic))
                
            # Sort descending by cumulative score safely
            scored_relics.sort(key=lambda x: x[0], reverse=True)
            
            if len(scored_relics) > 0:
                best_relic = scored_relics[0][1]
                best_relic_id = best_relic.get("id") if isinstance(best_relic, dict) else None
                
                loadout = await manager.get_loadout()
                slots_equipped = loadout.get("slots", [])
                if not isinstance(slots_equipped, list):
                    slots_equipped = []
                    
                current_relic_id = None
                if len(slots_equipped) > slot_index:
                    curr_relic = slots_equipped[slot_index]
                    current_relic_id = curr_relic.get("id") if isinstance(curr_relic, dict) else None
                    
                if best_relic_id and best_relic_id != current_relic_id:
                    slot_names = ["Red", "Green", "Blue"]
                    slot_label = slot_names[slot_index] if slot_index < len(slot_names) else str(slot_index)
                    logger.info(f"[{bot_name}] Equipping best relic in slot {slot_label}...")
                    await manager.equip_relic(slot_index, best_relic_id)

async def run_single_bot(bot_name: str, api_key: str):
    """Asynchronous self-contained worker loop for each individual bot."""
    logger.info(f"Starting worker task for [ {bot_name} ]...")
    
    while True:
        # SYNC BARRIER: Wait until all allied bots are fully out of any matches
        while any(settings.ACTIVE_BOTS_IN_GAME.values()):
            await asyncio.sleep(1)
        
        # Flush shared databases to ensure clean slate for the upcoming new match
        settings.SHARED_LOOT_TARGETS.clear()
        settings.SOS_TARGETS.clear()
        settings.SHARED_VISITED_HISTORY.clear()
        settings.SHARED_ACTIVE_DEATHZONES.clear()
        settings.BOT_POSITIONS.clear()
        
        # Run out-of-game loadout optimizer before entering queue
        try:
            await auto_equip_lobby(api_key, bot_name)
        except Exception as e:
            logger.error(f"[{bot_name}] Auto-loadout optimization failed: {str(e)}")

        lobby = JoinHandler(api_key=api_key)
        logger.info(f"Agent [ {bot_name} ] joining queue [ {settings.ROOM_PREFERENCE.upper()} ]...")
        
        gameplay_socket, _ = await lobby.execute_join_flow(entry_type=settings.ROOM_PREFERENCE)
        
        if not gameplay_socket:
            logger.error(f"[{bot_name}] Matchmaking failed. Retrying in 10 seconds...")
            await asyncio.sleep(10)
            continue

        logger.info(f"[OK] Agent [ {bot_name} ] entered the arena!")
        
        # Mark this bot as actively playing
        settings.ACTIVE_BOTS_IN_GAME[bot_name] = True
        
        battle = AgentHandler(gameplay_socket, agent_name=bot_name)
        start_time = asyncio.get_event_loop().time()
        
        try:
            await battle.start_monitoring()
        except KeyboardInterrupt:
            logger.info(f"Manual shutdown triggered for {bot_name}.")
            break
        except Exception as e:
            logger.error(f"[{bot_name}] Error during monitoring: {str(e)}")
        finally:
            # Mark this bot as inactive immediately upon match termination/death
            settings.ACTIVE_BOTS_IN_GAME[bot_name] = False
            try:
                await gameplay_socket.close()
            except Exception:
                pass

        session_duration = asyncio.get_event_loop().time() - start_time
        if session_duration < 5:
            logger.warning(f"[{bot_name}] Connection dropped prematurely. Sleeping 10 seconds...")
            await asyncio.sleep(10)
            continue

        if not battle.is_alive:
            logger.info(f"[{bot_name}] Waiting for other squad members to finish...")
            # Loop restarts, but barrier will block entering queue until the remaining bot dies/ends

async def start_bot():
    """Validates configuration and launches parallel asynchronous bot tasks."""
    logger.info("Checking configuration files...")
    try:
        settings.validate_config()
    except ValueError as e:
        logger.error(f"\033[91mFailed: {str(e)}\033[0m")
        return

    try:
        from config import game_data
        logger.info("\033[92mGame database assets loaded successfully.\033[0m")
    except Exception as e:
        logger.error(f"\033[91mFailed to load game database assets: {str(e)}\033[0m")
        return

    # Create asynchronous tasks for all configured active bots
    tasks = []
    for bot in settings.BOTS:
        tasks.append(run_single_bot(bot["name"], bot["api_key"]))

    if not tasks:
        logger.error("No active bots configured in .env. Please check NUM_BOTS and BOTx_ keys.")
        return

    # Launch all bots concurrently under a single execution process
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    if sys.platform == "win32":
        os.system("")
        
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("Bot execution stopped.")
        sys.exit(0)