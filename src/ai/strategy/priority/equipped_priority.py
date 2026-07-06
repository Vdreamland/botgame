from src.game_data import WEAPONS, ARMOR

class EquippedPriority:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        self_data = view.get("self", {})
        inventory = self_data.get("inventory", [])
        
        equipped_weapon = self_data.get("equippedWeapon")
        equipped_armor = self_data.get("equippedArmor")
        
        eq_weapon_name = equipped_weapon.get("name") if isinstance(equipped_weapon, dict) else (equipped_weapon if equipped_weapon else "None")
        eq_armor_name = equipped_armor.get("name") if isinstance(equipped_armor, dict) else (equipped_armor if equipped_armor else "None")
        
        melee_names = ["Fist", "Dagger", "Sword", "Katana"]
        ranged_names = ["Bow", "Pistol", "Sniper rifle"]
        
        best_melee_id = None
        best_melee_atk = WEAPONS.get(eq_weapon_name, {}).get("atk", 0) if eq_weapon_name in melee_names else 0
        
        best_ranged_id = None
        best_ranged_atk = WEAPONS.get(eq_weapon_name, {}).get("atk", 0) if eq_weapon_name in ranged_names else 0
        
        # Determine best available items in inventory
        for item in inventory:
            name = item.get("name")
            item_id = item.get("id")
            if not item_id or not name:
                continue
                
            if name in WEAPONS:
                atk = WEAPONS[name].get("atk", 0)
                if name in melee_names:
                    if atk > best_melee_atk:
                        best_melee_atk = atk
                        best_melee_id = item_id
                elif name in ranged_names:
                    if atk > best_ranged_atk:
                        best_ranged_atk = atk
                        best_ranged_id = item_id
                        
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
                    
        # Combat context check: Is there any enemy in Layer 0?
        current_region_id = view.get("currentRegion", {}).get("id")
        visible_agents = view.get("visibleAgents", [])
        visible_monsters = view.get("visibleMonsters", [])
        my_id = self_data.get("id")
        
        has_layer_0_enemies = False
        for agent in visible_agents:
            if agent.get("id") != my_id and agent.get("regionId") == current_region_id and agent.get("isAlive", True):
                has_layer_0_enemies = True
                break
                
        for monster in visible_monsters:
            if monster.get("regionId") == current_region_id and monster.get("isAlive", True):
                has_layer_0_enemies = True
                break
                
        # Dynamic weapon swapping logic
        if has_layer_0_enemies:
            # Under close combat, prefer best Melee weapon
            if best_melee_id and eq_weapon_name not in melee_names:
                return 100, {"action_type": "equip", "item_id": best_melee_id}
        else:
            # Under ranged/exploration, prefer overall highest ATK weapon
            if best_ranged_atk >= best_melee_atk:
                if best_ranged_id and eq_weapon_name != WEAPONS.get(best_ranged_id, {}):
                    return 100, {"action_type": "equip", "item_id": best_ranged_id}
            else:
                if best_melee_id and eq_weapon_name != WEAPONS.get(best_melee_id, {}):
                    return 100, {"action_type": "equip", "item_id": best_melee_id}
                    
        # Fallback to armor equip
        if best_armor_id:
            return 99, {"action_type": "equip", "item_id": best_armor_id}
            
        return 0, None