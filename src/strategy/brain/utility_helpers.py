from typing import List, Dict, Any, Tuple, Optional
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

ARMORS = {
    "Plate Armor": 3,
    "Chainmail": 2,
    "Leather Armor": 1
}

MELEE_WEAPONS = {
    "Katana": 40,
    "Sword": 24,
    "Dagger": 16,
    "Fist": 0
}

RANGED_WEAPONS = {
    "Sniper rifle": 32,
    "Pistol": 15,
    "Bow": 8
}

def count_backpack_and_slots(inventory: List[Any], equipped_weapon: Any, equipped_armor: Any) -> Tuple[int, int]:
    """Menghitung total slot tas ransel (mengabaikan sMoltz) dan total slot riil server."""
    backpack_count = 0
    for item in inventory:
        i_name = item.get("name") or item.get("displayName") or "" if isinstance(item, dict) else str(item)
        if i_name != "sMoltz":
            backpack_count += 1
            
    total_slots = backpack_count
    if equipped_weapon:
        total_slots += 1
    if equipped_armor:
        total_slots += 1
            
    return backpack_count, total_slots


def get_best_carried_gear(inventory: List[Any], equipped_weapon: Any) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[str], Optional[str]]:
    """Mendeteksi senjata Melee dan Ranged terbaik yang sedang dibawa, serta melacak ID senjata tumpuk tidak berguna."""
    eq_w_name = "None"
    eq_w_id = None
    if equipped_weapon:
        eq_w_name = equipped_weapon.get("name") if isinstance(equipped_weapon, dict) else str(equipped_weapon)
        eq_w_id = equipped_weapon.get("id") if isinstance(equipped_weapon, dict) else None

    carried_weapons = []
    if equipped_weapon:
        carried_weapons.append({"name": eq_w_name, "id": eq_w_id, "equipped": True})
        
    for item in inventory:
        if isinstance(item, dict):
            item_name = item.get("name") or item.get("displayName") or ""
            item_id = item.get("id") or item_name
        else:
            item_name = str(item)
            item_id = item_name

        if item_name in MELEE_WEAPONS or item_name in RANGED_WEAPONS:
            carried_weapons.append({"name": item_name, "id": item_id, "equipped": False})

    best_melee_val = -1
    best_melee_item = None
    best_ranged_val = -1
    best_ranged_item = None

    for w in carried_weapons:
        w_name = w["name"]
        if w_name in MELEE_WEAPONS:
            bonus = MELEE_WEAPONS[w_name]
            if bonus > best_melee_val:
                best_melee_val = bonus
                best_melee_item = w
        elif w_name in RANGED_WEAPONS:
            bonus = RANGED_WEAPONS[w_name]
            if bonus > best_ranged_val:
                best_ranged_val = bonus
                best_ranged_item = w

    # Cek jika ada senjata tumpuk berlebih yang bukan senjata terbaik kita
    redundant_weapon_id = None
    redundant_weapon_name = None
    for w in sorted(carried_weapons, key=lambda x: x["equipped"]):
        if w["equipped"]:
            continue
        w_name = w["name"]
        w_id = w["id"]
        
        is_best_melee = (best_melee_item and w_id == best_melee_item["id"])
        is_best_ranged = (best_ranged_item and w_id == best_ranged_item["id"])
        
        if (not is_best_melee) and (not is_best_ranged):
            redundant_weapon_id = w_id
            redundant_weapon_name = w_name
            break

    return best_melee_item, best_ranged_item, redundant_weapon_id, redundant_weapon_name