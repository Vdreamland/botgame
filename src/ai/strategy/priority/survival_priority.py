from src.game_data import GUARDIANS

class SurvivalPriority:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        self_data = view.get("self", {})
        my_id = self_data.get("id")
        
        hp = self_data.get("hp", 100)
        max_hp = self_data.get("maxHp", 100)
        hp_ratio = hp / max_hp if max_hp > 0 else 1.0
        
        my_atk = self_data.get("atk", 25)
        my_def = self_data.get("def", 5)
        
        equipped_weapon = self_data.get("equippedWeapon")
        eq_weapon_name = equipped_weapon.get("name") if isinstance(equipped_weapon, dict) else (equipped_weapon if equipped_weapon else "None")
        has_weapon = (eq_weapon_name not in ["None", "Fist"])
        
        current_region_id = view.get("currentRegion", {}).get("id")
        if not current_region_id:
            return 0, None
            
        visible_agents = view.get("visibleAgents", [])
        visible_monsters = view.get("visibleMonsters", [])
        
        has_layer_0_enemies = False
        unarmed_danger = False
        layer_0_player_count = 0
        
        has_dangerous_enemies = False
        layer_0_armed_count = 0
        layer_0_unarmed_count = 0
        layer_0_monster_count = 0
        has_guardian = False
        
        for agent in visible_agents:
            agent_id = agent.get("id")
            region_id = agent.get("regionId")
            if agent_id and agent_id != my_id and region_id == current_region_id:
                if agent.get("isAlive", True):
                    is_guard = (agent.get("isGuardian") or "guardian" in agent.get("name", "").lower())
                    if is_guard:
                        has_guardian = True
                        has_dangerous_enemies = True
                    else:
                        layer_0_player_count += 1
                        enemy_weapon = agent.get("weapon", "None")
                        enemy_has_weapon = (enemy_weapon not in ["None", "Fist"])
                        
                        target_atk = agent.get("atk", 25) if agent.get("atk") is not None else 25
                        target_def = agent.get("def", 5) if agent.get("def") is not None else 5
                        target_hp = agent.get("hp", 100)
                        
                        my_dmg = max(1, my_atk - target_def)
                        enemy_dmg = max(1, target_atk - my_def)
                        
                        turns_to_kill_enemy = (target_hp + my_dmg - 1) // my_dmg
                        turns_to_kill_me = (hp + enemy_dmg - 1) // enemy_dmg
                        
                        is_combat_feasible = (turns_to_kill_enemy < turns_to_kill_me) or (turns_to_kill_enemy <= 1)
                        
                        if enemy_has_weapon:
                            layer_0_armed_count += 1
                            if not is_combat_feasible:
                                has_dangerous_enemies = True
                        else:
                            layer_0_unarmed_count += 1
                            if hp < 20 and not is_combat_feasible:
                                has_dangerous_enemies = True
                            elif not has_weapon and target_hp > hp:
                                has_dangerous_enemies = True
                                
                    has_layer_0_enemies = True
                    
                enemy_weapon = agent.get("weapon", "None")
                enemy_has_weapon = (enemy_weapon not in ["None", "Fist"])
                if not has_weapon and enemy_has_weapon:
                    unarmed_danger = True
                    
        for monster in visible_monsters:
            monster_id = monster.get("id")
            region_id = monster.get("regionId")
            if monster_id and region_id == current_region_id:
                if monster.get("isAlive", True):
                    has_layer_0_enemies = True
                    monster_name = monster.get("name", "")
                    is_guard = (monster_name in GUARDIANS or "guardian" in monster_name.lower())
                    if is_guard:
                        has_guardian = True
                        has_dangerous_enemies = True
                    else:
                        layer_0_monster_count += 1
                        if hp < 30 or not has_weapon:
                            has_dangerous_enemies = True
                            
                    if not has_weapon:
                        if is_guard or hp < 50:
                            unarmed_danger = True
                            
        if layer_0_player_count >= 2:
            if layer_0_armed_count > 0 or hp < 40:
                return 97, {"action_type": "flee"}
                
        if hp_ratio < 0.4 and has_layer_0_enemies:
            if has_dangerous_enemies:
                return 97, {"action_type": "flee"}
                
        if unarmed_danger:
            return 92, {"action_type": "flee"}
            
        return 0, None