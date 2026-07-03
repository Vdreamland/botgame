from game_data.weapon_info import WEAPONS
from ai.detector.enemy_detector import get_visible_enemies_by_layer

MELEE_WEAPONS = {"Katana", "Sword", "Dagger"}
RANGED_WEAPONS = {"Sniper rifle", "Bow", "Pistol"}

def get_weapon_atk(w_name: str) -> int:
    return WEAPONS.get(w_name, {}).get("atk_bonus", 0)

def get_armour_def(a_name: str) -> int:
    ARMOURS = {
        "Plate Armor": 20,
        "Iron Armor": 10,
        "Leather Armor": 5
    }
    return ARMOURS.get(a_name, 0)

class EquippedPriority:
    def get_priorities(self, view: dict) -> list:
        priorities = []
        if not isinstance(view, dict):
            return priorities
        self_data = view.get("self", {})
        inventory = self_data.get("inventory", [])
        equipped_weapon = self_data.get("equippedWeapon")
        equipped_weapon_name = equipped_weapon.get("name", "Fist") if isinstance(equipped_weapon, dict) else "Fist"
        equipped_armor = self_data.get("equippedArmor")
        equipped_armor_name = equipped_armor.get("name", "None") if isinstance(equipped_armor, dict) else "None"

        self_bot_name = self_data.get("name", "self")
        layer_summary = get_visible_enemies_by_layer(view, self_bot_name)
        l0_counts = layer_summary.get(0, {}) if isinstance(layer_summary, dict) else {}
        l1_counts = layer_summary.get(1, {}) if isinstance(layer_summary, dict) else {}
        l2_counts = layer_summary.get(2, {}) if isinstance(layer_summary, dict) else {}
        
        enemies_l0 = l0_counts.get("P", 0) + l0_counts.get("M", 0)
        enemies_l1_l2 = l1_counts.get("P", 0) + l1_counts.get("M", 0) + l2_counts.get("P", 0) + l2_counts.get("M", 0)

        best_melee_in_inv = None
        best_melee_atk = 0
        best_ranged_in_inv = None
        best_ranged_atk = 0

        for item in inventory:
            if isinstance(item, dict):
                item_name = item.get("name", "None")
                if item_name in MELEE_WEAPONS:
                    atk = get_weapon_atk(item_name)
                    if atk > best_melee_atk:
                        best_melee_atk = atk
                        best_melee_in_inv = item
                elif item_name in RANGED_WEAPONS:
                    atk = get_weapon_atk(item_name)
                    if atk > best_ranged_atk:
                        best_ranged_atk = atk
                        best_ranged_in_inv = item

        best_armor_in_inv = None
        best_armor_def = get_armour_def(equipped_armor_name)

        for item in inventory:
            if isinstance(item, dict):
                item_name = item.get("name", "None")
                if item_name in {"Plate Armor", "Iron Armor", "Leather Armor"}:
                    armor_def = get_armour_def(item_name)
                    if armor_def > best_armor_def:
                        best_armor_def = armor_def
                        best_armor_in_inv = item

        for item in inventory:
            if isinstance(item, dict):
                item_id = item.get("id")
                item_name = item.get("name")
                score = 0.0

                if item_name in MELEE_WEAPONS or item_name in RANGED_WEAPONS:
                    if enemies_l0 > 0:
                        if item_name in MELEE_WEAPONS:
                            if best_melee_in_inv and item_name == best_melee_in_inv.get("name"):
                                if equipped_weapon_name not in MELEE_WEAPONS or get_weapon_atk(equipped_weapon_name) < best_melee_atk:
                                    score = 0.95
                        elif item_name in RANGED_WEAPONS:
                            score = 0.15
                    elif enemies_l1_l2 > 0:
                        if item_name in RANGED_WEAPONS:
                            if best_ranged_in_inv and item_name == best_ranged_in_inv.get("name"):
                                if equipped_weapon_name not in RANGED_WEAPONS or get_weapon_atk(equipped_weapon_name) < best_ranged_atk:
                                    score = 0.95
                        elif item_name in MELEE_WEAPONS:
                            score = 0.15
                    else:
                        best_atk_in_inv = max(best_melee_atk, best_ranged_atk)
                        if get_weapon_atk(item_name) == best_atk_in_inv:
                            if get_weapon_atk(equipped_weapon_name) < best_atk_in_inv:
                                score = 0.95

                elif item_name in {"Plate Armor", "Iron Armor", "Leather Armor"}:
                    if best_armor_in_inv and item_name == best_armor_in_inv.get("name"):
                        score = 0.95

                if item_id and item_name and score > 0.0:
                    priorities.append({
                        "id": item_id,
                        "name": item_name,
                        "score": score
                    })

        priorities.sort(key=lambda x: x["score"], reverse=True)
        return priorities

def get_equipment_priorities(view: dict) -> list:
    return EquippedPriority().get_priorities(view)