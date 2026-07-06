from math import ceil
from src.game_data import MONSTERS, GUARDIANS, WEAPONS

class TargetKillPriority:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        self_data = view.get("self", {})
        my_id = self_data.get("id")
        current_region_id = view.get("currentRegion", {}).get("id")
        
        if not current_region_id:
            return 0, None
            
        my_hp = self_data.get("hp", 100)
        my_ep = self_data.get("ep", 10)
        my_atk = self_data.get("atk", 25)
        my_def = self_data.get("def", 7)
        
        equipped_weapon = self_data.get("equippedWeapon")
        eq_weapon_name = equipped_weapon.get("name") if isinstance(equipped_weapon, dict) else (equipped_weapon if equipped_weapon else "None")
        has_weapon = (eq_weapon_name not in ["None", "Fist"])
        is_high_tier_weapon = (eq_weapon_name in ["Katana", "Sniper rifle"])
        
        weapon_data = WEAPONS.get(eq_weapon_name, {})
        weapon_range = weapon_data.get("range", 0)
        weapon_ep_cost = weapon_data.get("ep_cost", 1)
        
        if my_ep < weapon_ep_cost:
            return 0, None
            
        visible_agents = view.get("visibleAgents", [])
        visible_monsters = view.get("visibleMonsters", [])
        
        for agent in visible_agents:
            agent_id = agent.get("id")
            region_id = agent.get("regionId")
            if agent_id and agent_id != my_id:
                dist = manager.current_distances.get(region_id, 999) if manager.current_distances else (0 if region_id == current_region_id else 999)
                if dist <= weapon_range:
                    if agent.get("isAlive", True):
                        is_guard = (agent.get("isGuardian") or "guardian" in agent.get("name", "").lower())
                        
                        target_hp = agent.get("hp", 100)
                        max_hp_val = agent.get("maxHp", 100)
                        hp_ratio = target_hp / max_hp_val if max_hp_val > 0 else 1.0
                        
                        target_atk = agent.get("atk") if agent.get("atk") is not None else 25
                        target_def = agent.get("def") if agent.get("def") is not None else 5
                        
                        if not is_guard:
                            enemy_weapon = agent.get("weapon", "None")
                            enemy_has_weapon = (enemy_weapon not in ["None", "Fist"])
                            
                            if not has_weapon and hp_ratio >= 0.3:
                                continue
                                
                            if not has_weapon and not enemy_has_weapon and hp_ratio >= 0.5:
                                continue
                                
                        my_dmg = max(1, my_atk - target_def)
                        target_dmg = max(1, target_atk - my_def)
                        
                        my_ttk = (target_hp + my_dmg - 1) // my_dmg
                        target_ttk = (my_hp + target_dmg - 1) // target_dmg
                        
                        combat_feasible = (my_ttk < target_ttk) or (my_ttk <= 2)
                        if not combat_feasible:
                            continue
                            
                        if hp_ratio < 0.3:
                            return 98, {"action_type": "attack", "target_id": agent_id, "target_type": "agent", "target_region_id": region_id}
                            
                        if is_guard:
                            return 85, {"action_type": "attack", "target_id": agent_id, "target_type": "agent", "target_region_id": region_id}
                        return 93, {"action_type": "attack", "target_id": agent_id, "target_type": "agent", "target_region_id": region_id}
                        
        for monster in visible_monsters:
            monster_id = monster.get("id")
            region_id = monster.get("regionId")
            dist = manager.current_distances.get(region_id, 999) if manager.current_distances else (0 if region_id == current_region_id else 999)
            
            if dist <= weapon_range:
                monster_name = monster.get("name", "")
                if monster_id:
                    if monster.get("isAlive", True):
                        target_hp = monster.get("hp", 100)
                        max_hp_val = monster.get("maxHp", 100)
                        hp_ratio = target_hp / max_hp_val if max_hp_val > 0 else 1.0
                        
                        is_guard = (monster_name in GUARDIANS or max_hp_val >= 50 or "guardian" in monster_name.lower())
                        
                        if not has_weapon:
                            if is_guard or my_hp < 50 or hp_ratio >= 0.3:
                                continue
                                
                        base_stats = MONSTERS.get(monster_name, GUARDIANS.get(monster_name, {"atk": 25, "def": 5}))
                        target_atk = monster.get("atk") if monster.get("atk") is not None else base_stats.get("atk", 25)
                        target_def = monster.get("def") if monster.get("def") is not None else base_stats.get("def", 5)
                        
                        my_dmg = max(1, my_atk - target_def)
                        target_dmg = max(1, target_atk - my_def)
                        
                        turns_to_kill_target = (target_hp + my_dmg - 1) // my_dmg
                        turns_to_kill_me = (my_hp + target_dmg - 1) // target_dmg
                        
                        combat_feasible = (turns_to_kill_target < turns_to_kill_me) or (turns_to_kill_target <= 2)
                        if not combat_feasible:
                            continue
                            
                        if hp_ratio < 0.3:
                            return 98, {"action_type": "attack", "target_id": monster_id, "target_type": "monster", "target_region_id": region_id}
                            
                        if is_guard:
                            return 85, {"action_type": "attack", "target_id": monster_id, "target_type": "monster", "target_region_id": region_id}
                        return 77, {"action_type": "attack", "target_id": monster_id, "target_type": "monster", "target_region_id": region_id}
                        
        return 0, None