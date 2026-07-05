from game_data.weapon_info import WEAPONS
from game_data.armour_info import ARMOUR_GRADES

MELEE_WEAPONS = {"Katana", "Sword", "Dagger"}
RANGED_WEAPONS = {"Sniper rifle", "Bow", "Pistol"}
ARMOURS = {"Plate Armor", "Iron Armor", "Leather Armor", "Chainmail"}

def get_weapon_atk(w_name: str) -> int:
    return WEAPONS.get(w_name, {}).get("atk_bonus", 0)

def get_armour_def(a_name: str) -> int:
    ARMOURS_TO_GRADE = {
        "Plate Armor": "Epic",
        "Chainmail": "Rare",
        "Iron Armor": "Rare",
        "Leather Armor": "Common"
    }
    grade = ARMOURS_TO_GRADE.get(a_name)
    if grade:
        return ARMOUR_GRADES.get(grade, {}).get("estimated_def_bonus", 0)
    for grade_name, spec in ARMOUR_GRADES.items():
        if grade_name.lower() in a_name.lower():
            return spec.get("estimated_def_bonus", 0)
    return 0

async def clean_redundant_items(self_data_temp: dict, ws_client, turn_num: int, coordinator, bot_name: str) -> bool:
    if not isinstance(self_data_temp, dict):
        return False
    inventory = self_data_temp.get("inventory", [])
    if not isinstance(inventory, list) or not inventory:
        return False

    already_acted = ws_client.last_acted_turn == turn_num
    is_local_cooldown = coordinator.bots_state[bot_name].get("local_cooldown", False)
    if already_acted or is_local_cooldown:
        return False

    equipped_weapon = self_data_temp.get("equippedWeapon")
    equipped_weapon_name = equipped_weapon.get("name", "Fist") if isinstance(equipped_weapon, dict) else "Fist"
    equipped_armor = self_data_temp.get("equippedArmor")
    equipped_armor_name = equipped_armor.get("name", "None") if isinstance(equipped_armor, dict) else "None"

    best_melee_atk = get_weapon_atk(equipped_weapon_name) if equipped_weapon_name in MELEE_WEAPONS else 0
    best_melee_name = equipped_weapon_name if equipped_weapon_name in MELEE_WEAPONS else None

    best_ranged_atk = get_weapon_atk(equipped_weapon_name) if equipped_weapon_name in RANGED_WEAPONS else 0
    best_ranged_name = equipped_weapon_name if equipped_weapon_name in RANGED_WEAPONS else None

    best_armor_def = get_armour_def(equipped_armor_name)
    best_armor_name = equipped_armor_name if equipped_armor_name != "None" else None

    for item in inventory:
        if isinstance(item, dict):
            item_name = item.get("name")
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
            elif item_name in ARMOURS or any(g in item_name for g in ARMOUR_GRADES):
                def_val = get_armour_def(item_name)
                if def_val > best_armor_def:
                    best_armor_def = def_val
                    best_armor_name = item_name

    kept_melee = False
    kept_ranged = False
    kept_armor = False

    if equipped_weapon_name in MELEE_WEAPONS and equipped_weapon_name == best_melee_name:
        kept_melee = True
    if equipped_weapon_name in RANGED_WEAPONS and equipped_weapon_name == best_ranged_name:
        kept_ranged = True
    if equipped_armor_name != "None" and equipped_armor_name == best_armor_name:
        kept_armor = True

    for item in inventory:
        if isinstance(item, dict):
            item_name = item.get("name")
            item_id = item.get("id")
            is_melee = item_name in MELEE_WEAPONS
            is_ranged = item_name in RANGED_WEAPONS
            is_armor = item_name in ARMOURS or any(g in item_name for g in ARMOUR_GRADES)

            if is_melee:
                if item_name == best_melee_name and not kept_melee:
                    kept_melee = True
                else:
                    from ai.Strategy.memory import add_recent_event
                    add_recent_event(f"Dropped redundant weapon: {item_name}")
                    wrapped_payload = {
                        "type": "action",
                        "data": {"type": "drop", "itemId": item_id}
                    }
                    await ws_client.send(wrapped_payload)
                    return True
            elif is_ranged:
                if item_name == best_ranged_name and not kept_ranged:
                    kept_ranged = True
                else:
                    from ai.Strategy.memory import add_recent_event
                    add_recent_event(f"Dropped redundant weapon: {item_name}")
                    wrapped_payload = {
                        "type": "action",
                        "data": {"type": "drop", "itemId": item_id}
                    }
                    await ws_client.send(wrapped_payload)
                    return True
            elif is_armor:
                if item_name == best_armor_name and not kept_armor:
                    kept_armor = True
                else:
                    from ai.Strategy.memory import add_recent_event
                    add_recent_event(f"Dropped redundant armour: {item_name}")
                    wrapped_payload = {
                        "type": "action",
                        "data": {"type": "drop", "itemId": item_id}
                    }
                    await ws_client.send(wrapped_payload)
                    return True
    return False