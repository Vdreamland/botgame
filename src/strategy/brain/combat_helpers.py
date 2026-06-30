from typing import Dict, Any, List, Tuple
from config.game_data import WEAPONS

def get_weapons_and_range(view_self: Dict[str, Any], ep: int, inventory: List[Any]) -> Tuple[List[str], int, str]:
    """Mengidentifikasi semua senjata yang mampu dibeli dengan sisa EP dan mengukur range maksimal."""
    equipped_weapon = view_self.get("equippedWeapon")
    equipped_weapon_name = "None"
    if equipped_weapon:
        equipped_weapon_name = equipped_weapon.get("name") if isinstance(equipped_weapon, dict) else str(equipped_weapon)

    weapons_we_have = []
    
    eq_cost = WEAPONS.get(equipped_weapon_name, {}).get("ep_cost", 1) if equipped_weapon_name in WEAPONS else 1
    if ep >= eq_cost:
        weapons_we_have.append(equipped_weapon_name)
    else:
        if ep >= 1:
            weapons_we_have.append("Fist")

    for item in inventory:
        if isinstance(item, dict):
            item_name = item.get("name") or item.get("displayName") or ""
        else:
            item_name = str(item)

        if item_name in WEAPONS:
            cost = WEAPONS[item_name].get("ep_cost", 1)
            if ep >= cost:
                weapons_we_have.append(item_name)

    max_available_range = 0
    has_sniper = "Sniper rifle" in weapons_we_have
    has_ranged = any(w in ["Bow", "Pistol"] for w in weapons_we_have)
    has_melee = any(w in ["Katana", "Sword", "Dagger", "Fist"] for w in weapons_we_have)

    if has_sniper:
        max_available_range = 2
    elif has_ranged:
        max_available_range = 1
    elif has_melee:
        max_available_range = 0

    return weapons_we_have, max_available_range, equipped_weapon_name


def estimate_hits_to_kill(target: Dict[str, Any], our_atk: int) -> float:
    """Menghitung estimasi jumlah hit yang diperlukan untuk membunuh target dengan menghitung mitigasi DEF."""
    t_name = target["name"]
    t_hp = target["hp"]
    t_def = 5  # Default baseline DEF untuk pemain lain
    
    if target["is_monster"]:
        if "Wolf" in t_name:
            t_def = 1
        elif "Bear" in t_name:
            t_def = 3
        elif "Bandit" in t_name:
            t_def = 5
        elif "Guardian" in t_name:
            t_def = 34
            
    damage = max(1, our_atk - t_def)
    return t_hp / damage