from src.game_data import WEAPONS, ARMOR, RECOVERY_ITEMS, UTILITY_ITEMS

class GroundLootPriority:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        self_data = view.get("self", {})
        inventory = self_data.get("inventory", [])
        
        if len(inventory) >= 10:
            return 0, None
            
        equipped_weapon = self_data.get("equippedWeapon")
        eq_weapon_name = equipped_weapon.get("name") if isinstance(equipped_weapon, dict) else (equipped_weapon if equipped_weapon else "None")
        
        equipped_armor = self_data.get("equippedArmor")
        eq_armor_name = equipped_armor.get("name") if isinstance(equipped_armor, dict) else (equipped_armor if equipped_armor else "None")
        
        current_best_weapon_atk = WEAPONS.get(eq_weapon_name, {}).get("atk", 0)
        for item in inventory:
            name = item.get("name")
            if name in WEAPONS:
                atk = WEAPONS[name].get("atk", 0)
                if atk > current_best_weapon_atk:
                    current_best_weapon_atk = atk
                    
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
            
        weapon_candidates = []
        smoltz_candidates = []
        armor_candidates = []
        consumable_candidates = []
        utility_candidates = []
        
        for item in ground_items:
            name = item.get("name")
            item_id = item.get("id")
            if not name or not item_id:
                continue
                
            if name == "sMoltz":
                smoltz_candidates.append(item_id)
            elif name in WEAPONS:
                atk = WEAPONS[name].get("atk", 0)
                if atk > current_best_weapon_atk:
                    weapon_candidates.append(item_id)
            elif name in ARMOR:
                defense = ARMOR[name].get("def", 0)
                if defense > current_best_armor_def:
                    armor_candidates.append(item_id)
            elif name in RECOVERY_ITEMS:
                consumable_candidates.append(item_id)
            elif name in UTILITY_ITEMS:
                utility_candidates.append(item_id)
                
        if weapon_candidates:
            return 90, {"action_type": "loot", "item_id": weapon_candidates[0]}
        if smoltz_candidates:
            return 85, {"action_type": "loot", "item_id": smoltz_candidates[0]}
        if armor_candidates:
            return 80, {"action_type": "loot", "item_id": armor_candidates[0]}
        if consumable_candidates:
            return 70, {"action_type": "loot", "item_id": consumable_candidates[0]}
        if utility_candidates:
            return 65, {"action_type": "loot", "item_id": utility_candidates[0]}
            
        return 0, None