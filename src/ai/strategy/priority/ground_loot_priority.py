from src.game_data import WEAPONS, ARMOR, RECOVERY_ITEMS, UTILITY_ITEMS

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
        
        melee_names = ["Fist", "Dagger", "Sword", "Katana"]
        ranged_names = ["Bow", "Pistol", "Sniper rifle"]
        
        # 1. Cari Status Senjata & Armor Terbaik Mutlak (Equipped + Tas)
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
                    
        # 2. Sisihkan Barang Rongsokan / Duplikat (Spare)
        keep_melee = 1 if best_melee_name and best_melee_name != eq_weapon_name else 0
        keep_ranged = 1 if best_ranged_name and best_ranged_name != eq_weapon_name else 0
        keep_armor = 1 if best_armor_name and best_armor_name != eq_armor_name else 0
        
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
        
        # 3. Hitung Kebutuhan Recovery Items
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
        
        current_region = view.get("currentRegion", {})
        current_region_id = current_region.get("id")
        visible_regions = view.get("visibleRegions", [])
        
        my_region_data = next((r for r in visible_regions if r.get("id") == current_region_id), {})
        if not my_region_data:
            my_region_data = current_region
        
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
        
        # 4. Berbagi Barang ke Tim (Bagi Pakai)
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
        
        # 5. Pembuangan Proaktif Barang Rongsokan (Agar Tas Efektif)
        if not has_layer_0_agents:
            if spare_armors:
                junk_id, junk_name = spare_armors[0]
                return 80, {"action_type": "discard", "item_id": junk_id, "item_name": junk_name}
            if spare_weapons:
                junk_id, junk_name = spare_weapons[0]
                return 80, {"action_type": "discard", "item_id": junk_id, "item_name": junk_name}
        
        if not ground_items:
            return 0, None
        
        # 6. Pemindaian Ground Loot (Abaikan Barang Inferior)
        smoltz_candidates = []
        ground_armors = []
        consumable_candidates = []
        hp_consumable_candidates = []
        ep_consumable_candidates = []
        utility_candidates = []
        
        weapons_lower = {k.lower(): k for k in WEAPONS}
        armor_lower = {k.lower(): k for k in ARMOR}
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
                if defense > best_armor_def:
                    ground_armors.append((item_id, defense))
            elif name_lower in recovery_lower:
                consumable_candidates.append(item_id)
                if recovery_lower[name_lower].get("hp_heal", 0) > 0:
                    hp_consumable_candidates.append(item_id)
                if recovery_lower[name_lower].get("ep_heal", 0) > 0:
                    ep_consumable_candidates.append(item_id)
            elif name_lower in utility_lower:
                orig_name = utility_lower[name_lower]
                if orig_name not in inventory_item_names:
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
                    if atk > best_melee_atk:
                        ground_weapons.append((item_id, atk))
                elif name_lower in ranged_names_lower:
                    if atk > best_ranged_atk:
                        ground_weapons.append((item_id, atk))
        
        if ground_weapons:
            ground_weapons.sort(key=lambda x: x[1], reverse=True)
            weapon_candidates = [w[0] for w in ground_weapons]
        else:
            weapon_candidates = []
        
        wants_ep = bool(ep_consumable_candidates and ep_consumables_in_inv == 0)
        wants_hp = bool(hp_consumable_candidates and hp_consumables_in_inv == 0)
        
        has_valuable_ground_upgrade = bool(
            weapon_candidates or
            armor_candidates or
            smoltz_candidates or
            (utility_candidates and "binoculars" in [i.get("name", "").lower() for i in ground_items]) or
            (hp_consumable_candidates and hp_ratio < 0.6) or
            wants_ep or
            wants_hp
        )
        
        # 7. Pembuangan Khusus Saat Tas Penuh Penuh (10/10)
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
                    atk = WEAPONS[name].get("atk", 0)
                    is_best = False
                    if name in melee_names:
                        if atk == best_melee_atk:
                            is_best = True
                    elif name in ranged_names:
                        if atk == best_ranged_atk:
                            is_best = True
                    
                    if name == eq_weapon_name or is_best:
                        val = 90
                    else:
                        val = 10
                elif name in ARMOR:
                    defense = ARMOR[name].get("def", 0)
                    if name == eq_armor_name or defense == best_armor_def:
                        val = 90
                    else:
                        val = 10
                elif name in RECOVERY_ITEMS:
                    name_lower = name.lower()
                    is_hp_item = recovery_lower.get(name_lower, {}).get("hp_heal", 0) > 0
                    is_ep_item = recovery_lower.get(name_lower, {}).get("ep_heal", 0) > 0
                    
                    if is_hp_item and hp_consumables_in_inv > 1 and wants_ep:
                        val = 15
                    elif is_ep_item and ep_consumables_in_inv > 1 and wants_hp:
                        val = 15
                    else:
                        val = 20 if name == "Bandage" else 30
                
                if val < lowest_val:
                    lowest_val = val
                    lowest_item_id = item_id
                    lowest_item_name = name
            
            if lowest_item_id and lowest_val < 90:
                discard_score = 92 if has_layer_0_agents else 98
                if hp_consumable_candidates and hp_ratio <= 0.4:
                    discard_score = 101
                elif lowest_val == 15 and (wants_ep or wants_hp):
                    discard_score = 76 if has_layer_0_agents else 97
                return discard_score, {"action_type": "discard", "item_id": lowest_item_id, "item_name": lowest_item_name}
            return 0, None
        
        # 8. Skor Pengambilan (Loot) Barang di Lantai
        if hp_consumable_candidates and hp_ratio <= 0.4:
            return 101, {"action_type": "loot", "item_id": hp_consumable_candidates[0]}
            
        if smoltz_candidates:
            loot_score = 99 if has_layer_0_agents else 102
            return loot_score, {"action_type": "loot", "item_id": smoltz_candidates[0]}
        if weapon_candidates:
            loot_score = 97 if has_layer_0_agents else 99
            return loot_score, {"action_type": "loot", "item_id": weapon_candidates[0]}
        if armor_candidates:
            loot_score = 97 if has_layer_0_agents else 99
            return loot_score, {"action_type": "loot", "item_id": armor_candidates[0]}
            
        if wants_ep:
            loot_score = 75 if has_layer_0_agents else 96
            return loot_score, {"action_type": "loot", "item_id": ep_consumable_candidates[0]}
        if wants_hp:
            loot_score = 75 if has_layer_0_agents else 96
            return loot_score, {"action_type": "loot", "item_id": hp_consumable_candidates[0]}
            
        if utility_candidates:
            loot_score = 75 if has_layer_0_agents else 95
            return loot_score, {"action_type": "loot", "item_id": utility_candidates[0]}
        if consumable_candidates:
            loot_score = 70 if has_layer_0_agents else 95
            return loot_score, {"action_type": "loot", "item_id": consumable_candidates[0]}
        
        return 0, None