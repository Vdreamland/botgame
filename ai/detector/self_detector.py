from game_data.player_info import INVENTORY_LIMIT
from game_data.weapon_info import WEAPONS
from game_data.armour_info import ARMOUR_GRADES

def get_self_vital_status(view: dict) -> dict:
    status = {
        "hp": 100,
        "max_hp": 100,
        "ep": 10,
        "max_ep": 10,
        "atk": 25,
        "def": 5,
        "vision": 1.0,
        "is_hp_low": False,
        "is_ep_low": False,
        "alert_gauge": 0,
        "alert_active": False
    }
    if not isinstance(view, dict):
        return status
    self_data = view.get("self", {})
    if isinstance(self_data, dict):
        status["hp"] = self_data.get("hp", 100)
        status["max_hp"] = self_data.get("max_hp", 100)
        status["ep"] = self_data.get("ep", 10)
        status["max_ep"] = self_data.get("max_ep", 10)
        status["atk"] = self_data.get("atk", 25)
        status["def"] = self_data.get("def", 5)
        status["vision"] = float(self_data.get("vision", 1.0))
        status["is_hp_low"] = status["hp"] <= 30
        status["is_ep_low"] = status["ep"] <= 2
        status["alert_gauge"] = self_data.get("alertGauge", 0)
        status["alert_active"] = bool(self_data.get("alertActive", False))
    return status

def check_inventory_full(view: dict) -> bool:
    if not isinstance(view, dict):
        return False
    inventory = view.get("inventory", [])
    return len(inventory) >= INVENTORY_LIMIT

def check_better_equipments_in_inventory(view: dict) -> dict:
    result = {
        "better_weapon_found": False,
        "best_weapon_name": None,
        "better_armour_found": False,
        "best_armour_name": None
    }
    if not isinstance(view, dict):
        return result
    eq_weapon = view.get("equippedWeapon")
    curr_weapon_name = eq_weapon.get("name", "Fist") if isinstance(eq_weapon, dict) else "Fist"
    curr_weapon_bonus = WEAPONS.get(curr_weapon_name, {}).get("atk_bonus", 0)
    eq_armour = view.get("equippedArmor")
    curr_armour_name = eq_armour.get("name", "None") if isinstance(eq_armour, dict) else "None"
    curr_armour_bonus = 0
    if curr_armour_name != "None":
        for grade, spec in ARMOUR_GRADES.items():
            if grade.lower() in curr_armour_name.lower():
                curr_armour_bonus = spec.get("estimated_def_bonus", 0)
                break
    best_w_name = None
    best_w_bonus = curr_weapon_bonus
    best_a_name = None
    best_a_bonus = curr_armour_bonus
    inventory = view.get("inventory", [])
    if isinstance(inventory, list):
        for item in inventory:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            i_type = item.get("type", "").lower()
            if not name:
                continue
            if i_type == "weapon" or name in WEAPONS:
                bonus = WEAPONS.get(name, {}).get("atk_bonus", 0)
                if bonus > best_w_bonus:
                    best_w_bonus = bonus
                    best_w_name = name
            elif i_type == "armour" or "armor" in i_type or any(g in name for g in ARMOUR_GRADES):
                item_bonus = 0
                for grade, spec in ARMOUR_GRADES.items():
                    if grade.lower() in name.lower():
                        item_bonus = spec.get("estimated_def_bonus", 0)
                        break
                if item_bonus > best_a_bonus:
                    best_a_bonus = item_bonus
                    best_a_name = name
    if best_w_name:
        result["better_weapon_found"] = True
        result["best_weapon_name"] = best_w_name
    if best_a_name:
        result["better_armour_found"] = True
        result["best_armour_name"] = best_a_name
    return result