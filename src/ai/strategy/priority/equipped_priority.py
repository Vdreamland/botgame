from src.game_data import WEAPONS, ARMOR

class EquippedPriority:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        self_data = view.get("self", {})
        inventory = self_data.get("inventory", [])
        my_ep = self_data.get("ep", 10)
        
        equipped_weapon = self_data.get("equippedWeapon")
        equipped_armor = self_data.get("equippedArmor")
        
        eq_weapon_name = equipped_weapon.get("name") if isinstance(equipped_weapon, dict) else (equipped_weapon if equipped_weapon else "None")
        eq_armor_name = equipped_armor.get("name") if isinstance(equipped_armor, dict) else (equipped_armor if equipped_armor else "None")
        
        current_ep_cost = WEAPONS.get(eq_weapon_name, {}).get("ep_cost", 1) if eq_weapon_name in WEAPONS else 1
        
        melee_names = ["Fist", "Dagger", "Sword", "Katana"]
        ranged_names = ["Bow", "Pistol", "Sniper rifle"]
        
        is_melee_equipped = eq_weapon_name in melee_names
        is_ranged_equipped = eq_weapon_name in ranged_names
        
        max_melee_atk_available = 0
        best_melee_inv_id = None
        
        if is_melee_equipped and my_ep >= current_ep_cost:
            max_melee_atk_available = WEAPONS.get(eq_weapon_name, {}).get("atk", 0)
            
        max_ranged_atk_available = 0
        best_ranged_inv_id = None
        
        if is_ranged_equipped and my_ep >= current_ep_cost:
            max_ranged_atk_available = WEAPONS.get(eq_weapon_name, {}).get("atk", 0)
            
        emergency_weapon_id = None
        
        for item in inventory:
            name = item.get("name")
            item_id = item.get("id")
            if not item_id or not name:
                continue
                
            if name in WEAPONS:
                atk = WEAPONS[name].get("atk", 0)
                cost = WEAPONS[name].get("ep_cost", 1)
                
                if my_ep >= cost:
                    if not emergency_weapon_id:
                        emergency_weapon_id = item_id
                        
                    if name in melee_names:
                        if atk > max_melee_atk_available:
                            max_melee_atk_available = atk
                            best_melee_inv_id = item_id
                    elif name in ranged_names:
                        if atk > max_ranged_atk_available:
                            max_ranged_atk_available = atk
                            best_ranged_inv_id = item_id
                            
        best_armor_id = None
        best_armor_def = ARMOR.get(eq_armor_name, {}).get("def", 0)
        for item in inventory:
            name = item.get("name")
            item_id = item.get("id")
            if name in ARMOR:
                defense = ARMOR[name].get("def", 0)
                if defense > best_armor_def:
                    best_armor_def = defense
                    best_armor_id = item_id
                    
        has_layer_0_enemies = getattr(manager, "has_layer_0_enemies", False)
        has_nearby_enemies = getattr(manager, "has_nearby_enemies", False)
        has_outer_enemies = has_nearby_enemies and not has_layer_0_enemies
        
        if has_layer_0_enemies or has_outer_enemies:
            if my_ep < current_ep_cost and emergency_weapon_id:
                return 100, {"action_type": "equip", "item_id": emergency_weapon_id}
                
        if has_layer_0_enemies:
            if max_melee_atk_available > 0:
                if best_melee_inv_id:
                    return 100, {"action_type": "equip", "item_id": best_melee_inv_id}
            elif max_ranged_atk_available > 0:
                if best_ranged_inv_id:
                    return 100, {"action_type": "equip", "item_id": best_ranged_inv_id}
        else:
            if max_ranged_atk_available > 0:
                if best_ranged_inv_id:
                    return 100, {"action_type": "equip", "item_id": best_ranged_inv_id}
            elif max_melee_atk_available > 0:
                if best_melee_inv_id:
                    return 100, {"action_type": "equip", "item_id": best_melee_inv_id}
                    
        if best_armor_id:
            return 100, {"action_type": "equip", "item_id": best_armor_id}
            
        return 0, None