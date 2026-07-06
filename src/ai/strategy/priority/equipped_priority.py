from src.game_data import WEAPONS, ARMOR

class EquippedPriority:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        self_data = view.get("self", {})
        inventory = view.get("inventory", [])
        
        equipped_weapon = self_data.get("equippedWeapon")
        equipped_armor = self_data.get("equippedArmor")
        
        eq_weapon_name = equipped_weapon.get("name") if isinstance(equipped_weapon, dict) else (equipped_weapon if equipped_weapon else "None")
        eq_armor_name = equipped_armor.get("name") if isinstance(equipped_armor, dict) else (equipped_armor if equipped_armor else "None")
        
        current_weapon_atk = WEAPONS.get(eq_weapon_name, {}).get("atk", 0)
        current_armor_def = ARMOR.get(eq_armor_name, {}).get("def", 0)
        
        best_weapon_id = None
        best_weapon_atk = current_weapon_atk
        
        best_armor_id = None
        best_armor_def = current_armor_def
        
        for item in inventory:
            name = item.get("name")
            item_id = item.get("id")
            if not item_id or not name:
                continue
                
            if name in WEAPONS:
                atk = WEAPONS[name].get("atk", 0)
                if atk > best_weapon_atk:
                    best_weapon_atk = atk
                    best_weapon_id = item_id
            elif name in ARMOR:
                defense = ARMOR[name].get("def", 0)
                if defense > best_armor_def:
                    best_armor_def = defense
                    best_armor_id = item_id
                    
        if best_weapon_id:
            return 90, {"action_type": "equip", "item_id": best_weapon_id}
            
        if best_armor_id:
            return 85, {"action_type": "equip", "item_id": best_armor_id}
            
        return 0, None