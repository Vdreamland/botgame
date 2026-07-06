from math import ceil
from src.game_data import MONSTERS, GUARDIANS

class TargetKillPriority:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        self_data = view.get("self", {})
        my_id = self_data.get("id")
        current_region_id = view.get("currentRegion", {}).get("id")
        
        if not current_region_id:
            return 0, None
            
        my_hp = self_data.get("hp", 100)
        my_atk = self_data.get("atk", 25)
        my_def = self_data.get("def", 7)
        
        equipped_weapon = self_data.get("equippedWeapon")
        eq_weapon_name = equipped_weapon.get("name") if isinstance(equipped_weapon, dict) else (equipped_weapon if equipped_weapon else "None")
        has_weapon = (eq_weapon_name not in ["None", "Fist"])
        
        visible_agents = view.get("visibleAgents", [])
        visible_monsters = view.get("visibleMonsters", [])
        
        for agent in visible_agents:
            agent_id = agent.get("id")
            region_id = agent.get("regionId")
            if agent_id and agent_id != my_id and region_id == current_region_id:
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
                        if not has_weapon and not enemy_has_weapon and hp_ratio >= 0.5:
                            continue
                            
                    my_dmg = max(1, my_atk - target_def)
                    target_dmg = max(1, target_atk - my_def)
                    
                    my_ttk = ceil(target_hp / my_dmg)
                    target_ttk = ceil(my_hp / target_dmg)
                    
                    combat_feasible = (my_ttk < target_ttk) or (my_ttk <= 2)
                    if not combat_feasible:
                        continue
                        
                    if hp_ratio < 0.3:
                        return 98, {"action_type": "attack", "target_id": agent_id, "target_type": "agent"}
                        
                    if is_guard:
                        return 85, {"action_type": "attack", "target_id": agent_id, "target_type": "agent"}
                    return 93, {"action_type": "attack", "target_id": agent_id, "target_type": "agent"}
                    
        for monster in visible_monsters:
            monster_id = monster.get("id")
            region_id = monster.get("regionId")
            if dist := manager.current_distances.get(region_id):
                if dist > 0:
                    continue
                    
            monster_name = monster.get("name", "")
            if monster_id and region_id == current_region_id:
                if monster.get("isAlive", True):
                    target_hp = monster.get("hp", 100)
                    max_hp_val = monster.get("maxHp", 100)
                    hp_ratio = target_hp / max_hp_val if max_hp_val > 0 else 1.0
                    
                    is_guard = (monster_name in GUARDIANS or max_hp_val >= 50 or "guardian" in monster_name.lower())
                    
                    base_stats = MONSTERS.get(monster_name, GUARDIANS.get(monster_name, {"atk": 25, "def": 5}))
                    target_atk = monster.get("atk") if monster.get("atk") is not None else base_stats.get("atk", 25)
                    target_def = monster.get("def") if monster.get("def") is not None else base_stats.get("def", 5)
                    
                    my_dmg = max(1, my_atk - target_def)
                    target_dmg = max(1, target_atk - my_def)
                    
                    my_ttk = ceil(target_hp / my_dmg)
                    target_ttk = ceil(my_hp / target_dmg)
                    
                    combat_feasible = (my_ttk < target_ttk) or (my_ttk <= 2)
                    if not combat_feasible:
                        continue
                        
                    if hp_ratio < 0.3:
                        return 98, {"action_type": "attack", "target_id": monster_id, "target_type": "monster"}
                        
                    if is_guard:
                        return 85, {"action_type": "attack", "target_id": monster_id, "target_type": "monster"}
                    return 77, {"action_type": "attack", "target_id": monster_id, "target_type": "monster"}
                    
        return 0, None