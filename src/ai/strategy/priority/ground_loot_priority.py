from src.game_data import WEAPONS, ARMOR, RECOVERY_ITEMS
from src.ai.strategy.priority.loot_helper import analyze_inventory, analyze_ground_items

class GroundLootPriority:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        self_data = view.get("self", {})
        inventory = self_data.get("inventory", [])
        my_name = self_data.get("name", "Unknown")
        my_hp = self_data.get("hp", 100)
        max_hp = self_data.get("maxHp", 100)
        hp_ratio = my_hp / max_hp if max_hp > 0 else 1.0
        
        equipped_weapon = self_data.get("equippedWeapon")
        eq_weapon_name = equipped_weapon.get("name") if isinstance(equipped_weapon, dict) else (equipped_weapon if equipped_weapon else "None")
        
        equipped_armor = self_data.get("equippedArmor")
        eq_armor_name = equipped_armor.get("name") if isinstance(equipped_armor, dict) else (equipped_armor if equipped_armor else "None")
        
        inv_stats = analyze_inventory(inventory, eq_weapon_name, eq_armor_name)
        
        current_region_id = view.get("currentRegion", {}).get("id")
        visible_regions = view.get("visibleRegions", [])
        my_region_data = next((r for r in visible_regions if r.get("id") == current_region_id), view.get("currentRegion", {}))
        ground_items = my_region_data.get("items", [])
        
        game_id = getattr(manager, "game_id", None)
        team_states = manager.memory.get_team_states(current_game_id=game_id) if hasattr(manager, "memory") else {}
        teammates_in_region = []
        is_leader = True
        
        for name, t_state in team_states.items():
            if name != my_name:
                if name < my_name:
                    is_leader = False
                if t_state.get("region_id") == current_region_id:
                    teammate_weapon = t_state.get("weapon", "None")
                    has_no_good_weapon = (teammate_weapon in ["None", "Fist", "Bow"])
                    teammates_in_region.append({
                        "name": name,
                        "unarmed": has_no_good_weapon,
                        "state": t_state
                    })
        
        has_layer_0_agents = getattr(manager, "has_layer_0_agents", False)
        
        spare_weapons = inv_stats["spare_weapons"]
        spare_armors = inv_stats["spare_armors"]
        
        if spare_weapons and teammates_in_region:
            for teammate in teammates_in_region:
                if teammate["unarmed"]:
                    best_spare_id, best_spare_name = spare_weapons[0]
                    for item_id, name in spare_weapons:
                        if name == "Katana" or name == "Sniper rifle":
                            best_spare_id, best_spare_name = item_id, name
                            break
                    discard_score = 76 if has_layer_0_agents else 94
                    return discard_score, {"action_type": "discard", "item_id": best_spare_id, "item_name": best_spare_name}
        
        if not is_leader and spare_armors and team_states:
            for name, t_state in team_states.items():
                if name != my_name and name < my_name:
                    if t_state.get("region_id") == current_region_id:
                        leader_inv = t_state.get("inventory", [])
                        leader_item_names = [item.get("name") if isinstance(item, dict) else item for item in leader_inv]
                        leader_equipped_armor = t_state.get("armor", "None")
                        if "Plate Armor" not in leader_item_names and leader_equipped_armor != "Plate Armor":
                            for s_id, s_name in spare_armors:
                                if s_name == "Plate Armor":
                                    discard_score = 76 if has_layer_0_agents else 94
                                    return discard_score, {"action_type": "discard", "item_id": s_id, "item_name": s_name}
        
        if not has_layer_0_agents:
            if spare_armors:
                junk_id, junk_name = spare_armors[0]
                return 80, {"action_type": "discard", "item_id": junk_id, "item_name": junk_name}
            if spare_weapons:
                junk_id, junk_name = spare_weapons[0]
                return 80, {"action_type": "discard", "item_id": junk_id, "item_name": junk_name}
        
        if not ground_items:
            return 0, None
            
        ground_stats = analyze_ground_items(ground_items, inv_stats, hp_ratio)
        
        if len(inventory) >= 10:
            if not ground_stats["has_valuable"]:
                return 0, None
            
            lowest_val = 999
            lowest_item_id = None
            lowest_item_name = None
            
            melee_names = ["Fist", "Dagger", "Sword", "Katana"]
            ranged_names = ["Bow", "Pistol", "Sniper rifle"]
            recovery_lower = {k.lower(): v for k, v in RECOVERY_ITEMS.items()}
            
            for item in inventory:
                name = item.get("name")
                item_id = item.get("id")
                if not name or not item_id:
                    continue
                
                val = 50
                if name == "sMoltz":
                    val = 100
                elif name in WEAPONS:
                    atk = WEAPONS[name].get("atk", 0)
                    is_best = False
                    if name in melee_names:
                        if atk == inv_stats["best_melee_atk"]:
                            is_best = True
                    elif name in ranged_names:
                        if atk == inv_stats["best_ranged_atk"]:
                            is_best = True
                    
                    if name == eq_weapon_name or is_best:
                        val = 90
                    else:
                        val = 10
                elif name in ARMOR:
                    defense = ARMOR[name].get("def", 0)
                    if name == eq_armor_name or defense == inv_stats["best_armor_def"]:
                        val = 90
                    else:
                        val = 10
                elif name in RECOVERY_ITEMS:
                    name_lower = name.lower()
                    is_hp_item = recovery_lower.get(name_lower, {}).get("hp_heal", 0) > 0
                    is_ep_item = recovery_lower.get(name_lower, {}).get("ep_heal", 0) > 0
                    
                    if is_hp_item and inv_stats["hp_consumables_in_inv"] > 1 and ground_stats["wants_ep"]:
                        val = 15
                    elif is_ep_item and inv_stats["ep_consumables_in_inv"] > 1 and ground_stats["wants_hp"]:
                        val = 15
                    else:
                        val = 20 if name == "Bandage" else 30
                
                if val < lowest_val:
                    lowest_val = val
                    lowest_item_id = item_id
                    lowest_item_name = name
            
            if lowest_item_id and lowest_val < 90:
                discard_score = 92 if has_layer_0_agents else 98
                if ground_stats["hp_consumables"] and hp_ratio <= 0.4:
                    discard_score = 101
                elif lowest_val == 15 and (ground_stats["wants_ep"] or ground_stats["wants_hp"]):
                    discard_score = 76 if has_layer_0_agents else 97
                return discard_score, {"action_type": "discard", "item_id": lowest_item_id, "item_name": lowest_item_name}
            return 0, None
        
        if ground_stats["hp_consumables"] and hp_ratio <= 0.4:
            return 101, {"action_type": "loot", "item_id": ground_stats["hp_consumables"][0]}
            
        if ground_stats["smoltz"]:
            loot_score = 99 if has_layer_0_agents else 102
            return loot_score, {"action_type": "loot", "item_id": ground_stats["smoltz"][0]}
        if ground_stats["weapons"]:
            loot_score = 97 if has_layer_0_agents else 99
            return loot_score, {"action_type": "loot", "item_id": ground_stats["weapons"][0]}
        if ground_stats["armors"]:
            loot_score = 97 if has_layer_0_agents else 99
            return loot_score, {"action_type": "loot", "item_id": ground_stats["armors"][0]}
            
        if ground_stats["wants_ep"]:
            loot_score = 75 if has_layer_0_agents else 96
            return loot_score, {"action_type": "loot", "item_id": ground_stats["ep_consumables"][0]}
        if ground_stats["wants_hp"]:
            loot_score = 75 if has_layer_0_agents else 96
            return loot_score, {"action_type": "loot", "item_id": ground_stats["hp_consumables"][0]}
            
        if ground_stats["utilities"]:
            loot_score = 75 if has_layer_0_agents else 95
            return loot_score, {"action_type": "loot", "item_id": ground_stats["utilities"][0]}
        if ground_stats["consumables"]:
            loot_score = 70 if has_layer_0_agents else 95
            return loot_score, {"action_type": "loot", "item_id": ground_stats["consumables"][0]}
        
        return 0, None