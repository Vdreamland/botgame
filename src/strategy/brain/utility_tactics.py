from typing import Dict, Any, Optional, List
from config.game_data import WEAPONS
from src.strategy.behaviors.utility_behavior import UtilityBehavior

# Mengimpor kamus data dan helper dari modul pendukung
from src.strategy.brain.utility_helpers import (
    LOOT_PRIORITY,
    ARMORS,
    MELEE_WEAPONS,
    RANGED_WEAPONS
)

def evaluate_ground_loot(
    total_slots: int,
    inventory: List[Any],
    ground_items: List[Any],
    best_melee_item: Optional[Dict[str, Any]],
    best_ranged_item: Optional[Dict[str, Any]],
    equipped_armor: Any,
    eq_w_id: Optional[str],
    eq_a_id: Optional[str],
    context: Any
) -> Optional[Dict[str, Any]]:
    """Mengevaluasi opsi jarahan di tanah dengan membatasi kepemilikan senjata maks 2 jenis terbaik."""
    prioritized_items = []
    for g_item in ground_items:
        if isinstance(g_item, dict):
            g_name = g_item.get("name") or g_item.get("displayName") or ""
            g_id = g_item.get("id") or g_name
        else:
            g_name = str(g_item)
            g_id = g_name

        priority = LOOT_PRIORITY.get(g_name, 1)
        prioritized_items.append((priority, g_name, g_id))

    prioritized_items.sort(key=lambda x: x[0], reverse=True)

    for priority, g_name, g_id in prioritized_items:
        if g_name == "sMoltz":
            context.last_action_type = "pickup"
            return UtilityBehavior.build_pickup_action(
                item_id=g_id,
                thought="Collecting free sMoltz currency."
            )

        # PENJARAHAN DENGAN BATAS MAKS 1 MELEE + 1 RANGED TERBAIK
        if total_slots < 10:
            if g_name in ["Medkit", "Emergency Food", "Bandage", "Energy drink", "Megaphone", "Map", "Binoculars", "Radio"]:
                context.last_action_type = "pickup"
                return UtilityBehavior.build_pickup_action(
                    item_id=g_id,
                    thought=f"Looting vital recovery/utility: {g_name}."
                )

            elif g_name in WEAPONS:
                g_bonus = WEAPONS.get(g_name, {}).get("atk_bonus", 0)
                
                # JALUR MELEE: Batasi maksimal 1 melee terbaik
                if g_name in MELEE_WEAPONS:
                    if (not best_melee_item) or (best_melee_item["name"] == "Fist"):
                        context.last_action_type = "pickup"
                        return UtilityBehavior.build_pickup_action(
                            item_id=g_id,
                            thought=f"Looting melee weapon: {g_name}."
                        )
                    else:
                        carried_melee_bonus = MELEE_WEAPONS.get(best_melee_item["name"], 0)
                        if g_bonus > carried_melee_bonus:
                            context.last_action_type = "drop"
                            return UtilityBehavior.build_drop_action(
                                item_id=best_melee_item["id"],
                                thought=f"Looting upgrade: Dropping weaker melee {best_melee_item['name']} (+{carried_melee_bonus} ATK) to make room for {g_name} (+{g_bonus} ATK)."
                            )
                        else:
                            continue
                            
                # JALUR RANGED: Batasi maksimal 1 ranged terbaik
                elif g_name in RANGED_WEAPONS:
                    if not best_ranged_item:
                        context.last_action_type = "pickup"
                        return UtilityBehavior.build_pickup_action(
                            item_id=g_id,
                            thought=f"Looting ranged weapon: {g_name}."
                        )
                    else:
                        carried_ranged_bonus = RANGED_WEAPONS.get(best_ranged_item["name"], 0)
                        if g_bonus > carried_ranged_bonus:
                            context.last_action_type = "drop"
                            return UtilityBehavior.build_drop_action(
                                item_id=best_ranged_item["id"],
                                thought=f"Looting upgrade: Dropping weaker ranged {best_ranged_item['name']} (+{carried_ranged_bonus} ATK) to make room for {g_name} (+{g_bonus} ATK)."
                            )
                        else:
                            continue

            elif "Armor" in g_name or g_name == "Chainmail" or g_name in ARMORS:
                carried_armors_count = 0
                if equipped_armor:
                    carried_armors_count += 1
                for item in inventory:
                    i_name = item.get("name") or item.get("displayName") or "" if isinstance(item, dict) else str(item)
                    if i_name in ARMORS:
                        carried_armors_count += 1
                
                if carried_armors_count < 1:
                    context.last_action_type = "pickup"
                    return UtilityBehavior.build_pickup_action(
                        item_id=g_id,
                        thought=f"Looting armor: {g_name}."
                    )
        else:
            lowest_inv_item = None
            lowest_prio = 999
            for item in inventory:
                i_name = item.get("name") or item.get("displayName") or "" if isinstance(item, dict) else str(item)
                i_id = item.get("id") or i_name if isinstance(item, dict) else str(item)
                
                if i_name == "sMoltz" or i_id == eq_w_id or i_id == eq_a_id:
                    continue
                    
                p = LOOT_PRIORITY.get(i_name, 1)
                if p < lowest_prio:
                    lowest_prio = p
                    lowest_inv_item = {"id": i_id, "name": i_name}
                    
            if lowest_inv_item and priority > lowest_prio:
                context.last_action_type = "drop"
                return UtilityBehavior.build_drop_action(
                    item_id=lowest_inv_item["id"],
                    thought=f"Inventory full. Dropping {lowest_inv_item['name']} to make room for {g_name}."
                )

    return None