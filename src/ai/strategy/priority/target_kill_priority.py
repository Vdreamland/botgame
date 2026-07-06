import os
from src.game_data import MONSTERS, GUARDIANS, WEAPONS

def get_ally_names(my_name):
    allies = set()
    for key, value in os.environ.items():
        if key.startswith("BOT") and key.endswith("_NAME"):
            if value and value != my_name:
                allies.add(value)
    return allies

class TargetKillPriority:
    def evaluate(self, manager, raw_data):
        manager.last_attack_target_id = None
        
        view = raw_data.get("view", {})
        self_data = view.get("self", {})
        my_id = self_data.get("id")
        my_name = self_data.get("name", "Unknown")
        current_region_id = view.get("currentRegion", {}).get("id")
        
        if not current_region_id:
            return 0, None
            
        my_hp = self_data.get("hp", 100)
        my_atk = self_data.get("atk", 25)
        my_def = self_data.get("def", 7)
        
        ally_names = get_ally_names(my_name)
        
        equipped_weapon = self_data.get("equippedWeapon")
        eq_weapon_name = equipped_weapon.get("name") if isinstance(equipped_weapon, dict) else (equipped_weapon if equipped_weapon else "None")
        has_weapon = (eq_weapon_name not in ["None", "Fist"])
        is_high_tier_weapon = (eq_weapon_name in ["Katana", "Sniper rifle"])
        
        weapon_data = WEAPONS.get(eq_weapon_name, {})
        weapon_range = weapon_data.get("range", 0)
        weapon_ep_cost = weapon_data.get("ep_cost", 1)
        
        my_atk_total = my_atk + weapon_data.get("atk", 0)
        
        if self_data.get("ep", 10) < weapon_ep_cost:
            return 0, None
            
        visible_agents = view.get("visibleAgents", [])
        visible_monsters = view.get("visibleMonsters", [])
        
        team_states = manager.memory.get_team_states() if hasattr(manager, "memory") else {}
        teammate_targets = set()
        for teammate, state in team_states.items():
            if teammate != my_name:
                t_id = state.get("target_id")
                if t_id:
                    teammate_targets.add(t_id)
                    
        for agent in visible_agents:
            agent_id = agent.get("id")
            region_id = agent.get("regionId")
            if agent_id and agent_id != my_id:
                agent_name = agent.get("name", "")
                if agent_name in ally_names:
                    continue
                    
                dist = manager.current_distances.get(region_id, 999) if manager.current_distances else (0 if region_id == current_region_id else 999)
                if dist <= weapon_range:
                    if agent.get("isAlive", True):
                        is_guard = (agent.get("isGuardian") or "guardian" in agent_name.lower())
                        
                        target_hp = agent.get("hp", 100)
                        max_hp_val = agent.get("maxHp", 100)
                        hp_ratio = target_hp / max_hp_val if max_hp_val > 0 else 1.0
                        
                        target_atk = agent.get("atk") if agent.get("atk") is not None else 25
                        target_def = agent.get("def") if agent.get("def") is not None else 5
                        
                        my_dmg = max(1, my_atk_total - target_def)
                        target_dmg = max(1, target_atk - my_def)
                        
                        turns_to_kill_enemy = (target_hp + my_dmg - 1) // my_dmg
                        turns_to_kill_me = (my_hp + target_dmg - 1) // target_dmg
                        
                        is_combat_feasible = (turns_to_kill_enemy < turns_to_kill_me) or (turns_to_kill_enemy <= 1)
                        if not is_combat_feasible:
                            continue
                        
                        if hp_ratio < 0.3:
                            manager.last_attack_target_id = agent_id
                            return 98, {"action_type": "attack", "target_id": agent_id, "target_type": "agent"}
                            
                        is_focus_target = (agent_id in teammate_targets)
                        if is_focus_target:
                            manager.last_attack_target_id = agent_id
                            score = 89 if is_guard else 96
                            return score, {"action_type": "attack", "target_id": agent_id, "target_type": "agent"}
                            
                        if is_guard:
                            manager.last_attack_target_id = agent_id
                            return 85, {"action_type": "attack", "target_id": agent_id, "target_type": "agent"}
                            
                        manager.last_attack_target_id = agent_id
                        return 93, {"action_type": "attack", "target_id": agent_id, "target_type": "agent"}
                        
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
                        
                        if is_guard:
                            is_focus_target = (monster_id in teammate_targets)
                            if hp_ratio >= 0.2:
                                if not is_focus_target or my_hp < 60:
                                    continue
                        
                        if not has_weapon:
                            if is_guard or my_hp < 50 or hp_ratio >= 0.3:
                                continue
                                
                        base_stats = MONSTERS.get(monster_name, GUARDIANS.get(monster_name, {"atk": 25, "def": 5}))
                        target_atk = monster.get("atk") if monster.get("atk") is not None else base_stats.get("atk", 25)
                        target_def = monster.get("def") if monster.get("def") is not None else base_stats.get("def", 5)
                        
                        my_dmg = max(1, my_atk_total - target_def)
                        target_dmg = max(1, target_atk - my_def)
                        
                        turns_to_kill_target = (target_hp + my_dmg - 1) // my_dmg
                        turns_to_kill_me = (my_hp + target_dmg - 1) // target_dmg
                        
                        combat_feasible = (turns_to_kill_target < turns_to_kill_me) or (turns_to_kill_target <= 2)
                        if not combat_feasible:
                            continue
                            
                        if hp_ratio < 0.3:
                            manager.last_attack_target_id = monster_id
                            return 98, {"action_type": "attack", "target_id": monster_id, "target_type": "monster", "target_region_id": region_id}
                            
                        is_focus_target = (monster_id in teammate_targets)
                        if is_focus_target:
                            manager.last_attack_target_id = monster_id
                            score = 89 if is_guard else 82
                            return score, {"action_type": "attack", "target_id": monster_id, "target_type": "monster", "target_region_id": region_id}
                            
                        if is_guard:
                            manager.last_attack_target_id = monster_id
                            return 85, {"action_type": "attack", "target_id": monster_id, "target_type": "monster", "target_region_id": region_id}
                            
                        manager.last_attack_target_id = monster_id
                        return 77, {"action_type": "attack", "target_id": monster_id, "target_type": "monster", "target_region_id": region_id}
                        
        return 0, None