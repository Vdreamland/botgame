class SurvivalPriority:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        self_data = view.get("self", {})
        my_id = self_data.get("id")
        
        hp = self_data.get("hp", 100)
        max_hp = self_data.get("maxHp", 100)
        hp_ratio = hp / max_hp if max_hp > 0 else 1.0
        
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
        
        for agent in visible_agents:
            agent_id = agent.get("id")
            region_id = agent.get("regionId")
            if agent_id and agent_id != my_id and region_id == current_region_id:
                if agent.get("isAlive", True):
                    is_guard = (agent.get("isGuardian") or "guardian" in agent.get("name", "").lower())
                    if not is_guard:
                        layer_0_player_count += 1
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
                    if not has_weapon:
                        unarmed_danger = True
                        
        if layer_0_player_count >= 2:
            return 97, {"action_type": "flee"}
            
        if hp_ratio < 0.4 and has_layer_0_enemies:
            return 97, {"action_type": "flee"}
            
        if unarmed_danger:
            return 92, {"action_type": "flee"}
            
        return 0, None