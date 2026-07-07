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
        
        candidates = []
        effective_range = min(1, weapon_range)
        
        for agent in visible_agents:
            agent_id = agent.get("id")
            region_id = agent.get("regionId")
            if agent_id and agent_id != my_id:
                agent_name = agent.get("name", "")
                if agent_name in ally_names:
                    continue
                
                dist = manager.current_distances.get(region_id, 999) if manager.current_distances else (0 if region_id == current_region_id else 999)
                if dist <= effective_range:
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
                            score = 98
                        else:
                            is_focus_target = (agent_id in teammate_targets)
                            if is_focus_target:
                                score = 89 if is_guard else 96
                            elif is_guard:
                                score = 85
                            else:
                                score = 93
                        
                        candidates.append({
                            "score": score,
                            "target_id": agent_id,
                            "target_type": "agent",
                            "region_id": region_id,
                            "dist": dist
                        })
        
        for monster in visible_monsters:
            monster_id = monster.get("id")
            region_id = monster.get("regionId")
            dist = manager.current_distances.get(region_id, 999) if manager.current_distances else (0 if region_id == current_region_id else 999)
            
            if dist <= effective_range:
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
                            score = 98
                        else:
                            is_focus_target = (monster_id in teammate_targets)
                            if is_focus_target:
                                score = 89 if is_guard else 82
                            elif is_guard:
                                score = 85
                            else:
                                score = 77
                        
                        candidates.append({
                            "score": score,
                            "target_id": monster_id,
                            "target_type": "monster",
                            "region_id": region_id,
                            "dist": dist
                        })
        
        layer_0_candidates = [c for c in candidates if c["dist"] == 0]
        if layer_0_candidates:
            layer_0_candidates.sort(key=lambda x: x["score"], reverse=True)
            best_target = layer_0_candidates[0]
            manager.last_attack_target_id = best_target["target_id"]
            if best_target["target_type"] == "agent":
                return best_target["score"], {"action_type": "attack", "target_id": best_target["target_id"], "target_type": "agent"}
            else:
                return best_target["score"], {"action_type": "attack", "target_id": best_target["target_id"], "target_type": "monster", "target_region_id": best_target["region_id"]}
        
        layer_1_candidates = [c for c in candidates if c["dist"] == 1]
        if layer_1_candidates:
            layer_1_candidates.sort(key=lambda x: x["score"], reverse=True)
            best_target = layer_1_candidates[0]
            manager.last_attack_target_id = best_target["target_id"]
            if best_target["target_type"] == "agent":
                return best_target["score"], {"action_type": "attack", "target_id": best_target["target_id"], "target_type": "agent"}
            else:
                return best_target["score"], {"action_type": "attack", "target_id": best_target["target_id"], "target_type": "monster", "target_region_id": best_target["region_id"]}
        
        return 0, None