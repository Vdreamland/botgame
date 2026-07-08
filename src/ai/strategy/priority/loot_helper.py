from src.game_data import WEAPONS, ARMOR, RECOVERY_ITEMS, UTILITY_ITEMS

def analyze_inventory(inventory, eq_weapon_name, eq_armor_name):
    melee_names = ["Fist", "Dagger", "Sword", "Katana"]
    ranged_names = ["Bow", "Pistol", "Sniper rifle"]
    
    best_melee_name = None
    best_melee_atk = 0
    best_ranged_name = None
    best_ranged_atk = 0
    best_armor_name = None
    best_armor_def = 0
    
    if eq_weapon_name in melee_names:
        best_melee_name = eq_weapon_name
        best_melee_atk = WEAPONS.get(eq_weapon_name, {}).get("atk", 0)
    elif eq_weapon_name in ranged_names:
        best_ranged_name = eq_weapon_name
        best_ranged_atk = WEAPONS.get(eq_weapon_name, {}).get("atk", 0)
        
    if eq_armor_name in ARMOR:
        best_armor_name = eq_armor_name
        best_armor_def = ARMOR.get(eq_armor_name, {}).get("def", 0)
        
    for item in inventory:
        name = item.get("name")
        if name in melee_names:
            atk = WEAPONS.get(name, {}).get("atk", 0)
            if atk > best_melee_atk:
                best_melee_atk = atk
                best_melee_name = name
        elif name in ranged_names:
            atk = WEAPONS.get(name, {}).get("atk", 0)
            if atk > best_ranged_atk:
                best_ranged_atk = atk
                best_ranged_name = name
        elif name in ARMOR:
            defense = ARMOR.get(name, {}).get("def", 0)
            if defense > best_armor_def:
                best_armor_def = defense
                best_armor_name = name
                
    keep_melee = 1 if best_melee_name else 0
    keep_ranged = 1 if best_ranged_name else 0
    keep_armor = 1 if best_armor_name else 0
    
    spare_weapons = []
    spare_armors = []
    for item in inventory:
        name = item.get("name")
        item_id = item.get("id")
        if name in melee_names:
            if name == best_melee_name and keep_melee > 0:
                keep_melee -= 1
            else:
                spare_weapons.append((item_id, name))
        elif name in ranged_names:
            if name == best_ranged_name and keep_ranged > 0:
                keep_ranged -= 1
            else:
                spare_weapons.append((item_id, name))
        elif name in ARMOR:
            if name == best_armor_name and keep_armor > 0:
                keep_armor -= 1
            else:
                spare_armors.append((item_id, name))
    
    recovery_lower = {k.lower(): v for k, v in RECOVERY_ITEMS.items()}
    inventory_item_names = {item.get("name") for item in inventory}
    
    hp_consumables_in_inv = 0
    ep_consumables_in_inv = 0
    
    for item in inventory:
        name = item.get("name")
        name_lower = name.lower() if name else ""
        if name_lower in recovery_lower:
            if recovery_lower[name_lower].get("hp_heal", 0) > 0:
                hp_consumables_in_inv += 1
            if recovery_lower[name_lower].get("ep_heal", 0) > 0:
                ep_consumables_in_inv += 1
                
    return {
        "best_melee_name": best_melee_name,
        "best_melee_atk": best_melee_atk,
        "best_ranged_name": best_ranged_name,
        "best_ranged_atk": best_ranged_atk,
        "best_armor_name": best_armor_name,
        "best_armor_def": best_armor_def,
        "spare_weapons": spare_weapons,
        "spare_armors": spare_armors,
        "hp_consumables_in_inv": hp_consumables_in_inv,
        "ep_consumables_in_inv": ep_consumables_in_inv,
        "inventory_item_names": inventory_item_names
    }

def analyze_ground_items(ground_items, inv_stats, hp_ratio):
    melee_names_lower = ["fist", "dagger", "sword", "katana"]
    ranged_names_lower = ["bow", "pistol", "sniper rifle"]
    
    smoltz_candidates = []
    ground_armors = []
    consumable_candidates = []
    hp_consumable_candidates = []
    ep_consumable_candidates = []
    utility_candidates = []
    ground_weapons = []
    
    weapons_lower = {k.lower(): k for k in WEAPONS}
    armor_lower = {k.lower(): k for k in ARMOR}
    utility_lower = {k.lower(): k for k in UTILITY_ITEMS}
    recovery_lower = {k.lower(): v for k, v in RECOVERY_ITEMS.items()}
    
    for item in ground_items:
        name = item.get("name")
        item_id = item.get("id")
        if not name or not item_id:
            continue
        
        name_lower = name.lower()
        
        if name_lower == "smoltz":
            smoltz_candidates.append(item_id)
        elif name_lower in armor_lower:
            orig_name = armor_lower[name_lower]
            defense = ARMOR[orig_name].get("def", 0)
            if defense > inv_stats["best_armor_def"]:
                ground_armors.append((item_id, defense))
        elif name_lower in recovery_lower:
            consumable_candidates.append(item_id)
            if recovery_lower[name_lower].get("hp_heal", 0) > 0:
                hp_consumable_candidates.append(item_id)
            if recovery_lower[name_lower].get("ep_heal", 0) > 0:
                ep_consumable_candidates.append(item_id)
        elif name_lower in utility_lower:
            orig_name = utility_lower[name_lower]
            if orig_name not in inv_stats["inventory_item_names"]:
                utility_candidates.append(item_id)
        elif name_lower in weapons_lower:
            orig_name = weapons_lower[name_lower]
            atk = WEAPONS[orig_name].get("atk", 0)
            if name_lower in melee_names_lower:
                if atk > inv_stats["best_melee_atk"]:
                    ground_weapons.append((item_id, atk))
            elif name_lower in ranged_names_lower:
                if atk > inv_stats["best_ranged_atk"]:
                    ground_weapons.append((item_id, atk))
                    
    if ground_armors:
        ground_armors.sort(key=lambda x: x[1], reverse=True)
        armor_candidates = [a[0] for a in ground_armors]
    else:
        armor_candidates = []
        
    if ground_weapons:
        ground_weapons.sort(key=lambda x: x[1], reverse=True)
        weapon_candidates = [w[0] for w in ground_weapons]
    else:
        weapon_candidates = []
        
    wants_ep = bool(ep_consumable_candidates and inv_stats["ep_consumables_in_inv"] == 0)
    wants_hp = bool(hp_consumable_candidates and inv_stats["hp_consumables_in_inv"] == 0)
    
    has_valuable = bool(
        weapon_candidates or
        armor_candidates or
        smoltz_candidates or
        (utility_candidates and "binoculars" in [i.get("name", "").lower() for i in ground_items]) or
        (hp_consumable_candidates and hp_ratio < 0.6) or
        wants_ep or
        wants_hp
    )
    
    return {
        "smoltz": smoltz_candidates,
        "armors": armor_candidates,
        "weapons": weapon_candidates,
        "consumables": consumable_candidates,
        "hp_consumables": hp_consumable_candidates,
        "ep_consumables": ep_consumable_candidates,
        "utilities": utility_candidates,
        "wants_ep": wants_ep,
        "wants_hp": wants_hp,
        "has_valuable": has_valuable
    }