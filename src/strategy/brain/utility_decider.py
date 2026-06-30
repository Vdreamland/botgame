from typing import Dict, Any, Optional
from src.strategy.brain.game_context import GameContext
from src.strategy.brain.base_decider import BaseDecider
from src.strategy.behaviors.utility_behavior import UtilityBehavior
from config.game_data import WEAPONS

# Mengimpor helper taktis dan pembantu penyaring dari modul baru
from src.strategy.brain.utility_helpers import (
    count_backpack_and_slots,
    get_best_carried_gear,
    ARMORS
)
from src.strategy.brain.utility_tactics import evaluate_ground_loot

class UtilityDecider(BaseDecider):
    
    def decide(self, view: Dict[str, Any], context: GameContext) -> Optional[Dict[str, Any]]:
        view_self = view.get("self", {})
        inventory = view_self.get("inventory", [])
        current_region = view.get("currentRegion", {})
        region_id = current_region.get("id")
        
        equipped_weapon = view_self.get("equippedWeapon")
        equipped_armor = view_self.get("equippedArmor")

        # 1. HITUNG TOTAL SLOT TAS RIIL (Menggunakan Helper)
        backpack_count, total_slots = count_backpack_and_slots(
            inventory=inventory, 
            equipped_weapon=equipped_weapon, 
            equipped_armor=equipped_armor
        )

        # 2. DETEKSI MELEE/RANGED TERBAIK & SINGKIRKAN REDUNDANT (Menggunakan Helper)
        best_melee_item, best_ranged_item, redundant_weapon_id, redundant_weapon_name = get_best_carried_gear(
            inventory=inventory,
            equipped_weapon=equipped_weapon
        )

        # Eksekusi aksi drop instan jika tas membawa senjata tumpuk berlebih yang tidak dipakai
        if redundant_weapon_id:
            context.last_action_type = "drop"
            return UtilityBehavior.build_drop_action(
                item_id=redundant_weapon_id,
                thought=f"Tactical inventory tidy-up: Dropping redundant/weaker weapon {redundant_weapon_name} to free slot."
            )

        # 3. EVALUASI EQUIP SENJATA LEBIH BAIK
        eq_w_name = "None"
        eq_w_id = None
        if equipped_weapon:
            eq_w_name = equipped_weapon.get("name") if isinstance(equipped_weapon, dict) else str(equipped_weapon)
            eq_w_id = equipped_weapon.get("id") if isinstance(equipped_weapon, dict) else None

        current_atk_bonus = -1
        if equipped_weapon:
            current_atk_bonus = WEAPONS.get(eq_w_name, {}).get("atk_bonus", 0)

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

        # 4. EVALUASI EQUIP ARMOR LEBIH BAIK
        current_armor_score = 0
        eq_a_id = None
        if equipped_armor:
            ar_name = equipped_armor.get("name") if isinstance(equipped_armor, dict) else str(equipped_armor)
            eq_a_id = equipped_armor.get("id") if isinstance(equipped_armor, dict) else None
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

        # 5. PENGGUNAAN ITEM PETA (MAP)
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

        # 6. MEMBUKA SUPPLY CACHE
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

        # 7. EVALUASI DAN EKSEKUSI PENJARAHAN DINAMIS (Menggunakan Taktik Baru)
        ground_items = current_region.get("items", [])
        if ground_items:
            looting_action = evaluate_ground_loot(
                total_slots=total_slots,
                inventory=inventory,
                ground_items=ground_items,
                best_melee_item=best_melee_item,
                best_ranged_item=best_ranged_item,
                equipped_armor=equipped_armor,
                eq_w_id=eq_w_id,
                eq_a_id=eq_a_id,
                context=context
            )
            if looting_action:
                return looting_action

        return None