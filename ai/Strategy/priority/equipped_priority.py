from ai.detector.ground_detector import detect_ground_loot
from game_data.weapon_info import WEAPONS
from game_data.armour_info import ARMOURS

MELEE_WEAPONS = {"Katana", "Sword", "Dagger"}
RANGED_WEAPONS = {"Sniper rifle", "Bow", "Pistol"}

def get_weapon_atk(w_name: str) -> int:
    return WEAPONS.get(w_name, {}).get("atk", 0)

def get_armour_def(a_name: str) -> int:
    return ARMOURS.get(a_name, {}).get("def", 0)

class GroundLootPriority:
    def get_priorities(self, view: dict) -> list:
        priorities = []
        if not isinstance(view, dict):
            return priorities
        current_region = view.get("currentRegion", {})
        if not isinstance(current_region, dict):
            return priorities
        items = current_region.get("items", [])
        if not isinstance(items, list):
            return priorities

        self_data = view.get("self", {})
        inventory = self_data.get("inventory", [])
        equipped_weapon = self_data.get("equippedWeapon")
        equipped_weapon_name = equipped_weapon.get("name", "Fist") if isinstance(equipped_weapon, dict) else "Fist"
        equipped_armor = self_data.get("equippedArmor")
        equipped_armor_name = equipped_armor.get("name", "None") if isinstance(equipped_armor, dict) else "None"

        best_melee_name = "Fist"
        best_melee_atk = get_weapon_atk(equipped_weapon_name) if equipped_weapon_name in MELEE_WEAPONS else 0
        best_ranged_name = "Fist"
        best_ranged_atk = get_weapon_atk(equipped_weapon_name) if equipped_weapon_name in RANGED_WEAPONS else 0

        for item in inventory:
            if isinstance(item, dict):
                item_name = item.get("name", "None")
                if item_name in MELEE_WEAPONS:
                    atk = get_weapon_atk(item_name)
                    if atk > best_melee_atk:
                        best_melee_atk = atk
                        best_melee_name = item_name
                elif item_name in RANGED_WEAPONS:
                    atk = get_weapon_atk(item_name)
                    if atk > best_ranged_atk:
                        best_ranged_atk = atk
                        best_ranged_name = item_name

        best_armor_name = equipped_armor_name
        best_armor_def = get_armour_def(equipped_armor_name)
        for item in inventory:
            if isinstance(item, dict):
                item_name = item.get("name", "None")
                if item_name in ARMOURS:
                    armor_def = get_armour_def(item_name)
                    if armor_def > best_armor_def:
                        best_armor_def = armor_def
                        best_armor_name = item_name

        for item in items:
            if isinstance(item, dict):
                item_id = item.get("id")
                item_name = item.get("name")
                item_type = item.get("type", "unknown")
                score = 0.0
                if item_name == "sMoltz":
                    score = 0.99
                elif item_type == "weapon":
                    if item_name in MELEE_WEAPONS:
                        atk = get_weapon_atk(item_name)
                        if atk > best_melee_atk:
                            score = 0.95
                        else:
                            score = 0.15
                    elif item_name in RANGED_WEAPONS:
                        atk = get_weapon_atk(item_name)
                        if atk > best_ranged_atk:
                            score = 0.95
                        else:
                            score = 0.15
                    else:
                        score = 0.15
                elif item_type == "armour":
                    armor_def = get_armour_def(item_name)
                    if armor_def > best_armor_def:
                        score = 0.95
                    else:
                        score = 0.15
                elif item_name in ("Medkit", "medkit"):
                    score = 0.85
                elif item_name == "Emergency Food":
                    score = 0.70
                elif item_name == "Bandage":
                    score = 0.70
                elif item_name == "Energy drink":
                    score = 0.70
                elif item_name == "Binoculars":
                    score = 0.30
                else:
                    score = 0.15

                if item_id and item_name:
                    priorities.append({
                        "id": item_id,
                        "name": item_name,
                        "score": score
                    })
        priorities.sort(key=lambda x: x["score"], reverse=True)
        return priorities