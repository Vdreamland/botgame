from src.game_data import MONSTERS, GUARDIANS

class TargetKillPriority:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        self_data = view.get("self", {})
        my_id = self_data.get("id")
        current_region_id = view.get("currentRegion", {}).get("id")
        
        if not current_region_id:
            return 0, None
            
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
                    enemy_weapon = agent.get("weapon", "None")
                    enemy_has_weapon = (enemy_weapon not in ["None", "Fist"])
                    hp_val = agent.get("hp", 100)
                    max_hp_val = agent.get("maxHp", 100)
                    hp_ratio = hp_val / max_hp_val if max_hp_val > 0 else 1.0
                    
                    if not has_weapon and hp_ratio >= 0.3:
                        continue
                        
                    if not has_weapon and not enemy_has_weapon and hp_ratio >= 0.5:
                        continue
                        
                    if hp_ratio < 0.3:
                        return 98, {"action_type": "attack", "target_id": agent_id, "target_type": "agent"}
                        
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
                    hp_val = monster.get("hp", 100)
                    max_hp_val = monster.get("maxHp", 100)
                    hp_ratio = hp_val / max_hp_val if max_hp_val > 0 else 1.0
                    
                    if not has_weapon and hp_ratio >= 0.3:
                        continue
                        
                    if hp_ratio < 0.3:
                        return 98, {"action_type": "attack", "target_id": monster_id, "target_type": "monster"}
                        
                    if monster_name in GUARDIANS:
                        return 85, {"action_type": "attack", "target_id": monster_id, "target_type": "monster"}
                    return 77, {"action_type": "attack", "target_id": monster_id, "target_type": "monster"}
                    
        return 0, None