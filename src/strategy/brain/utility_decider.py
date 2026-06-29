from typing import Dict, Any, Optional
from src.strategy.brain.game_context import GameContext
from src.strategy.brain.base_decider import BaseDecider
from src.strategy.behaviors.utility_behavior import UtilityBehavior
from config.game_data import WEAPONS

# Tabel skala prioritas pemungutan barang terlengkap (Mencakup sMoltz & seluruh Utility Items)
LOOT_PRIORITY = {
    "sMoltz": 11,           # Koin sMoltz (Skor tertinggi, tanpa memakan slot tas!)
    "Medkit": 10,
    "Katana": 9,
    "Sniper rifle": 9,
    "Plate Armor": 8,
    "Sword": 7,
    "Emergency Food": 6,
    "Binoculars": 5,        # Utility: Vision Boost +1 Pasif
    "Energy Drink": 5,
    "Bandage": 4,
    "Megaphone": 4,         # Utility: Megaphone item
    "Map": 4,               # Utility: Reveals entire map
    "Radio": 4,             # Utility: Long-range comms
    "Pistol": 3,
    "Bow": 2,
    "Dagger": 1
}

class UtilityDecider(BaseDecider):
    
    def decide(self, view: Dict[str, Any], context: GameContext) -> Optional[Dict[str, Any]]:
        view_self = view.get("self", {})
        inventory = view_self.get("inventory", [])
        current_region = view.get("currentRegion", {})
        
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
                item_name = item.get("name") or item.get("displayName", "")
                item_id = item.get("id", "")
                if item_name in WEAPONS and item_id:
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

        ground_items = current_region.get("items", [])
        if ground_items and len(inventory) < 10:
            
            carried_weapons = []
            carried_armors = []
            
            if equipped_weapon:
                w_name = equipped_weapon.get("name") if isinstance(equipped_weapon, dict) else str(equipped_weapon)
                carried_weapons.append({"name": w_name, "atk_bonus": current_atk_bonus})
                
            equipped_armor = view_self.get("equippedArmor")
            if equipped_armor:
                ar_name = equipped_armor.get("name") if isinstance(equipped_armor, dict) else str(equipped_armor)
                carried_armors.append({"name": ar_name})

            for item in inventory:
                if isinstance(item, dict):
                    item_name = item.get("name") or item.get("displayName", "")
                    if item_name in WEAPONS:
                        bonus = WEAPONS.get(item_name, {}).get("atk_bonus", 0)
                        carried_weapons.append({"name": item_name, "atk_bonus": bonus})
                    elif "Armor" in item_name:
                        carried_armors.append({"name": item_name})

            sorted_ground_items = []
            for g_item in ground_items:
                if isinstance(g_item, dict):
                    g_name = g_item.get("name") or g_item.get("displayName", "")
                    g_id = g_item.get("id", "")
                    if g_id:
                        priority_score = LOOT_PRIORITY.get(g_name, 0)
                        sorted_ground_items.append((priority_score, g_name, g_id))

            sorted_ground_items.sort(key=lambda x: x[0], reverse=True)

            for score, g_name, g_id in sorted_ground_items:
                if score == 0:
                    continue

                # Pengecekan khusus sMoltz (Selalu diprioritaskan utama karena tidak memakan kuota slot tas!)
                if g_name == "sMoltz":
                    context.last_action_type = "pickup"
                    return UtilityBehavior.build_pickup_action(
                        item_id=g_id,
                        thought="Collecting free sMoltz currency reward."
                    )

                # Kategori A: Item Medis & Item Utilitas (Diambil tanpa batasan angka 2)
                if g_name in ["Medkit", "Emergency Food", "Bandage", "Energy Drink", "Megaphone", "Map", "Binoculars", "Radio"]:
                    context.last_action_type = "pickup"
                    return UtilityBehavior.build_pickup_action(
                        item_id=g_id,
                        thought=f"Looting valuable utility/recovery item: {g_name}."
                    )

                # Kategori B: Senjata (Maksimal 2 senjata terbaik)
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

                # Kategori C: Armor (Maksimal 2 armor terbaik)
                elif "Armor" in g_name:
                    if len(carried_armors) < 2:
                        context.last_action_type = "pickup"
                        return UtilityBehavior.build_pickup_action(
                            item_id=g_id,
                            thought=f"Looting armor: {g_name}."
                        )

        return None