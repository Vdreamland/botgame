from typing import Dict, Any, Optional
from src.strategy.brain.game_context import GameContext
from src.strategy.brain.base_decider import BaseDecider
from src.strategy.behaviors.utility_behavior import UtilityBehavior
from config.game_data import WEAPONS

LOOT_PRIORITY = {
    "sMoltz": 11,
    "Medkit": 10,
    "Katana": 9,
    "Sniper rifle": 9,
    "Plate Armor": 8,
    "Sword": 7,
    "Emergency Food": 6,
    "Binoculars": 5,
    "Energy drink": 5,
    "Bandage": 4,
    "Megaphone": 4,
    "Map": 4,
    "Radio": 4,
    "Pistol": 3,
    "Bow": 2,
    "Dagger": 1
}

# Tabel kekuatan pelindung badan (Armor)
ARMORS = {
    "Plate Armor": 3,
    "Chainmail": 2,
    "Leather Armor": 1
}

class UtilityDecider(BaseDecider):
    
    def decide(self, view: Dict[str, Any], context: GameContext) -> Optional[Dict[str, Any]]:
        view_self = view.get("self", {})
        inventory = view_self.get("inventory", [])
        current_region = view.get("currentRegion", {})
        region_id = current_region.get("id")
        
        # Calculate real inventory slots consumed (ignoring sMoltz)
        real_inv_count = 0
        for item in inventory:
            i_name = item.get("name") or item.get("displayName") or "" if isinstance(item, dict) else str(item)
            if i_name != "sMoltz":
                real_inv_count += 1

        equipped_weapon = view_self.get("equippedWeapon")
        current_atk_bonus = -1
        if equipped_weapon:
            w_name = equipped_weapon.get("name") if isinstance(equipped_weapon, dict) else str(equipped_weapon)
            current_atk_bonus = WEAPONS.get(w_name, {}).get("atk_bonus", 0)

        best_weapon_id = None
        best_weapon_name = ""
        best_weapon_bonus = current_atk_bonus

        for item in inventory:
            if isinstance(item, dict):
                item_name = item.get("name") or item.get("displayName") or ""
                item_id = item.get("id") or item_name
            else:
                item_name = str(item)
                item_id = item_name

            if item_name in WEAPONS:
                atk_bonus = WEAPONS.get(item_name, {}).get("atk_bonus", 0)
                if atk_bonus > best_weapon_bonus:
                    best_weapon_bonus = atk_bonus
                    best_weapon_id = item_id
                    best_weapon_name = item_name

        if best_weapon_id:
            context.last_action_type = "equip"
            return UtilityBehavior.build_equip_action(
                item_id=best_weapon_id,
                thought=f"Equipping better weapon: {best_weapon_name} (+{best_weapon_bonus} ATK)."
            )

        # 1.1 LOGIKA PEMAKAIAN ARMOR TERBAIK OTOMATIS (0 EP, Free Action)
        equipped_armor = view_self.get("equippedArmor")
        current_armor_score = 0
        if equipped_armor:
            ar_name = equipped_armor.get("name") if isinstance(equipped_armor, dict) else str(equipped_armor)
            current_armor_score = ARMORS.get(ar_name, 0)

        best_armor_id = None
        best_armor_name = ""
        best_armor_score = current_armor_score

        for item in inventory:
            if isinstance(item, dict):
                item_name = item.get("name") or item.get("displayName") or ""
                item_id = item.get("id") or item_name
            else:
                item_name = str(item)
                item_id = item_name

            if item_name in ARMORS:
                score = ARMORS.get(item_name, 0)
                if score > best_armor_score:
                    best_armor_score = score
                    best_armor_id = item_id
                    best_armor_name = item_name

        if best_armor_id:
            context.last_action_type = "equip"
            return UtilityBehavior.build_equip_action(
                item_id=best_armor_id,
                thought=f"Equipping better armor: {best_armor_name}."
            )

        # 1.5 USE MAP UTILITY TO REMOVE FOG OF WAR
        for item in inventory:
            if isinstance(item, dict):
                item_name = item.get("name") or item.get("displayName") or ""
                item_id = item.get("id", "")
            else:
                item_name = str(item)
                item_id = item_name
            if item_name == "Map" and item_id:
                context.last_action_type = "use_item"
                return UtilityBehavior.build_use_item_action(
                    item_id=item_id,
                    thought="Using Map utility to permanently reveal all enemy positions."
                )

        # 2. FITUR PEMBONGKARAN PETI PERSEDIAAN OTOMATIS
        interactables = current_region.get("interactables", [])
        for fac in interactables:
            if isinstance(fac, dict):
                fac_name = fac.get("name", "")
                is_used = fac.get("isUsed", True)
                if fac_name == "Supply Cache" and not is_used:
                    already_interacted = any(
                        act.get("type") == "interact" and act.get("regionId") == region_id 
                        for act in context.history_actions
                    )
                    if not already_interacted:
                        context.last_action_type = "interact"
                        context.history_actions.append({"type": "interact", "regionId": region_id})
                        return UtilityBehavior.build_interact_action(
                            thought="Opening Supply Cache to secure valuable equipment loot."
                        )

        # 3. MEMUNGUT BARANG DI TANAH BERDASARKAN HIERARKI PRIORITAS
        ground_items = current_region.get("items", [])
        if ground_items:
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

            carried_weapons = []
            carried_armors = []
            
            if equipped_weapon:
                w_name = equipped_weapon.get("name") if isinstance(equipped_weapon, dict) else str(equipped_weapon)
                carried_weapons.append({"name": w_name, "atk_bonus": current_atk_bonus})
                
            if equipped_armor:
                ar_name = equipped_armor.get("name") if isinstance(equipped_armor, dict) else str(equipped_armor)
                carried_armors.append({"name": ar_name})

            for item in inventory:
                if isinstance(item, dict):
                    item_name = item.get("name") or item.get("displayName") or ""
                else:
                    item_name = str(item)

                if item_name in WEAPONS:
                    bonus = WEAPONS.get(item_name, {}).get("atk_bonus", 0)
                    carried_weapons.append({"name": item_name, "atk_bonus": bonus})
                elif "Armor" in item_name or item_name == "Chainmail" or item_name in ARMORS:
                    carried_armors.append({"name": item_name})

            # Identify currently equipped items to protect them from dropping
            eq_w_id = equipped_weapon.get("id") if isinstance(equipped_weapon, dict) else None
            eq_a_id = equipped_armor.get("id") if isinstance(equipped_armor, dict) else None

            for priority, g_name, g_id in prioritized_items:
                if g_name == "sMoltz":
                    context.last_action_type = "pickup"
                    return UtilityBehavior.build_pickup_action(
                        item_id=g_id,
                        thought="Collecting free sMoltz currency."
                    )

                if real_inv_count < 10:
                    if g_name in ["Medkit", "Emergency Food", "Bandage", "Energy drink", "Megaphone", "Map", "Binoculars", "Radio"]:
                        context.last_action_type = "pickup"
                        return UtilityBehavior.build_pickup_action(
                            item_id=g_id,
                            thought=f"Looting vital recovery/utility: {g_name}."
                        )

                    elif g_name in WEAPONS:
                        if len(carried_weapons) < 2:
                            context.last_action_type = "pickup"
                            return UtilityBehavior.build_pickup_action(
                                item_id=g_id,
                                thought=f"Looting weapon: {g_name}."
                            )
                        else:
                            g_bonus = WEAPONS.get(g_name, {}).get("atk_bonus", 0)
                            weakest_carried_weapon = min(carried_weapons, key=lambda x: x["atk_bonus"])
                            if g_bonus > weakest_carried_weapon["atk_bonus"]:
                                context.last_action_type = "pickup"
                                return UtilityBehavior.build_pickup_action(
                                    item_id=g_id,
                                    thought=f"Looting stronger weapon: {g_name} to replace {weakest_carried_weapon['name']}."
                                )

                    elif "Armor" in g_name or g_name == "Chainmail" or g_name in ARMORS:
                        if len(carried_armors) < 2:
                            context.last_action_type = "pickup"
                            return UtilityBehavior.build_pickup_action(
                                item_id=g_id,
                                thought=f"Looting armor: {g_name}."
                            )
                else:
                    # INVENTORY FULL LOGIC: Drop weak items to make room for high priority loot
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