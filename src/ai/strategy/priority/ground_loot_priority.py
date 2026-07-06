from src.game_data import WEAPONS, ARMOR, RECOVERY_ITEMS, UTILITY_ITEMS

class GroundLootPriority:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        self_data = view.get("self", {})
        inventory = self_data.get("inventory", [])
        
        equipped_weapon = self_data.get("equippedWeapon")
        eq_weapon_name = equipped_weapon.get("name") if isinstance(equipped_weapon, dict) else (equipped_weapon if equipped_weapon else "None")
        
        equipped_armor = self_data.get("equippedArmor")
        eq_armor_name = equipped_armor.get("name") if isinstance(equipped_armor, dict) else (equipped_armor if equipped_armor else "None")
        
        melee_names = ["Fist", "Dagger", "Sword", "Katana"]
        ranged_names = ["Bow", "Pistol", "Sniper rifle"]
        
        current_best_melee = WEAPONS.get(eq_weapon_name, {}).get("atk", 0) if eq_weapon_name in melee_names else 0
        current_best_ranged = WEAPONS.get(eq_weapon_name, {}).get("atk", 0) if eq_weapon_name in ranged_names else 0
        
        for item in inventory:
            name = item.get("name")
            if name in WEAPONS:
                atk = WEAPONS[name].get("atk", 0)
                if name in melee_names:
                    if atk > current_best_melee:
                        current_best_melee = atk
                elif name in ranged_names:
                    if atk > current_best_ranged:
                        current_best_ranged = atk
                        
        current_best_armor_def = ARMOR.get(eq_armor_name, {}).get("def", 0)
        for item in inventory:
            name = item.get("name")
            if name in ARMOR:
                defense = ARMOR[name].get("def", 0)
                if defense > current_best_armor_def:
                    current_best_armor_def = defense
                    
        current_region = view.get("currentRegion", {})
        current_region_id = current_region.get("id")
        visible_regions = view.get("visibleRegions", [])
        
        my_region_data = next((r for r in visible_regions if r.get("id") == current_region_id), {})
        if not my_region_data:
            my_region_data = current_region
            
        ground_items = my_region_data.get("items", [])
        if not ground_items:
            return 0, None
            
        smoltz_candidates = []
        ground_armors = []
        consumable_candidates = []
        utility_candidates = []
        
        weapons_lower = {k.lower(): k for k in WEAPONS}
        armor_lower = {k.lower(): k for k in ARMOR}
        recovery_lower = {k.lower(): k for k in RECOVERY_ITEMS}
        utility_lower = {k.lower(): k for k in UTILITY_ITEMS}
        
        melee_names_lower = [k.lower() for k in melee_names]
        ranged_names_lower = [k.lower() for k in ranged_names]
        
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
                if defense > current_best_armor_def:
                    ground_armors.append((item_id, defense))
            elif name_lower in recovery_lower:
                consumable_candidates.append(item_id)
            elif name_lower in utility_lower:
                utility_candidates.append(item_id)
                
        if ground_armors:
            ground_armors.sort(key=lambda x: x[1], reverse=True)
            armor_candidates = [a[0] for a in ground_armors]
        else:
            armor_candidates = []
            
        ground_weapons = []
        for item in ground_items:
            name = item.get("name")
            item_id = item.get("id")
            if not name or not item_id:
                continue
                
            name_lower = name.lower()
            if name_lower in weapons_lower:
                orig_name = weapons_lower[name_lower]
                atk = WEAPONS[orig_name].get("atk", 0)
                if name_lower in melee_names_lower:
                    if atk > current_best_melee:
                        ground_weapons.append((item_id, atk))
                elif name_lower in ranged_names_lower:
                    if atk > current_best_ranged:
                        ground_weapons.append((item_id, atk))
                        
        if ground_weapons:
            ground_weapons.sort(key=lambda x: x[1], reverse=True)
            weapon_candidates = [w[0] for w in ground_weapons]
        else:
            weapon_candidates = []
            
        has_valuable_ground_upgrade = bool(weapon_candidates or armor_candidates or (utility_candidates and "binoculars" in [i.get("name", "").lower() for i in ground_items]))
        
        if len(inventory) >= 10:
            if not has_valuable_ground_upgrade:
                return 0, None
                
            lowest_val = 999
            lowest_item_id = None
            lowest_item_name = None
            
            for item in inventory:
                name = item.get("name")
                item_id = item.get("id")
                if not name or not item_id:
                    continue
                    
                val = 50
                if name == "sMoltz":
                    val = 100
                elif name in WEAPONS:
                    if name == eq_weapon_name:
                        val = 90
                    else:
                        val = 10
                elif name in ARMOR:
                    if name == eq_armor_name:
                        val = 90
                    else:
                        val = 10
                elif name in RECOVERY_ITEMS:
                    val = 20 if name == "Bandage" else 30
                    
                if val < lowest_val:
                    lowest_val = val
                    lowest_item_id = item_id
                    lowest_item_name = name
                    
            if lowest_item_id and lowest_val < 90:
                return 88, {"action_type": "discard", "item_id": lowest_item_id, "item_name": lowest_item_name}
            return 0, None
            
        if weapon_candidates:
            return 90, {"action_type": "loot", "item_id": weapon_candidates[0]}
        if smoltz_candidates:
            return 85, {"action_type": "loot", "item_id": smoltz_candidates[0]}
        if armor_candidates:
            return 80, {"action_type": "loot", "item_id": armor_candidates[0]}
        if utility_candidates:
            return 75, {"action_type": "loot", "item_id": utility_candidates[0]}
        if consumable_candidates:
            return 70, {"action_type": "loot", "item_id": consumable_candidates[0]}
            
        return 0, None