# utility/strategy/combat_solver.py

from game_data.monster_info import MONSTERS
from game_data.weapon_info import WEAPONS
from game_data.armour_info import ARMOURS
from utility.detector.layer_detector import calculate_distances
from utility.detector.bot_stats_detector import detect_agent_stats
from utility.detector.zone_detector import detect_zone

def evaluate_combat_targets(bot_name: str, self_data: dict, current_region: dict, view_data: dict, joined_bots: list) -> dict:
    """Mensimulasikan kalkulasi damage dan menganalisis prioritas target pertempuran menggunakan detektor umum terpusat"""
    
    our_stats = detect_agent_stats(self_data)
    our_hp = our_stats["hp"]
    our_max_hp = our_stats["max_hp"]
    our_ep = our_stats["ep"]
    our_max_ep = our_stats["max_ep"]
    our_atk_stat = our_stats["atk"]
    our_def_stat = our_stats["def"]
    
    our_def_bonus = 0
    equipped_armor = self_data.get("equippedArmor")
    if isinstance(equipped_armor, dict):
        our_def_bonus = equipped_armor.get("defBonus") or equipped_armor.get("def_bonus") or 0
        if our_def_bonus == 0:
            our_a_name = (equipped_armor.get("name") or "").lower()
            for a_id, a_stats in ARMOURS.items():
                if a_id in our_a_name or a_stats.get("display_name", "").lower() in our_a_name:
                    our_def_bonus = a_stats.get("def_bonus", 0)
                    break
                    
    our_total_def = our_def_stat + our_def_bonus
    
    our_atk_bonus = 0
    our_weapon_range = 0
    our_weapon_ep_cost = 1
    
    equipped_weapon = self_data.get("equippedWeapon")
    weapon_key = "fist"
    if isinstance(equipped_weapon, dict):
        weapon_display = (equipped_weapon.get("displayName") or equipped_weapon.get("name") or "").lower()
        for w_id, w_stats in WEAPONS.items():
            if w_id in weapon_display or w_stats.get("display_name", "").lower() in weapon_display:
                weapon_key = w_id
                break
                
    weapon_stats = WEAPONS.get(weapon_key, WEAPONS["fist"])
    our_atk_bonus = weapon_stats.get("atk_bonus", 0)
    our_weapon_range = weapon_stats.get("range", 0)
    our_weapon_ep_cost = weapon_stats.get("ep_cost", 1)
    
    our_total_atk = our_atk_stat + our_atk_bonus
    
    distances = calculate_distances(current_region, view_data)
    analyzed_targets = []
    
    visible_agents = view_data.get("visibleAgents") or []
    for agent in visible_agents:
        if not isinstance(agent, dict):
            continue
            
        a_name = agent.get("name", "")
        if a_name == bot_name:
            continue
            
        t_stats = detect_agent_stats(agent)
        if not t_stats["is_alive"]:
            continue
            
        r_id = (
            agent.get("regionId") or 
            agent.get("region_id") or 
            agent.get("currentRegionId") or 
            agent.get("currentRegion", {}).get("id")
        )
        
        dist = distances.get(r_id)
        if dist is None:
            continue
            
        t_def_bonus = 0
        t_armor = agent.get("equippedArmor")
        if isinstance(t_armor, dict):
            t_def_bonus = t_armor.get("defBonus") or t_armor.get("def_bonus") or 0
            if t_def_bonus == 0:
                t_a_name = (t_armor.get("name") or "").lower()
                for a_id, a_stats in ARMOURS.items():
                    if a_id in t_a_name or a_stats.get("display_name", "").lower() in t_a_name:
                        t_def_bonus = a_stats.get("def_bonus", 0)
                        break
                        
        target_def = t_stats["def"] + t_def_bonus
        
        t_atk_bonus = 0
        t_weapon = agent.get("equippedWeapon")
        if isinstance(t_weapon, dict):
            t_w_display = (t_weapon.get("displayName") or t_weapon.get("name") or "").lower()
            for w_id, w_stats in WEAPONS.items():
                if w_stats.get("display_name", "").lower() in t_w_display or w_id in t_w_display:
                    t_atk_bonus = w_stats.get("atk_bonus", 0)
                    break
                    
        target_atk = t_stats["atk"] + t_atk_bonus
        target_hp = t_stats["hp"]
        
        damage_dealt = max(1, our_total_atk - target_def)
        damage_received = max(1, target_atk - our_total_def)
        
        is_in_range = dist <= our_weapon_range
        can_one_shot = target_hp <= damage_dealt
        
        is_player = False
        for j_bot in joined_bots:
            if j_bot.lower() in a_name.lower() or a_name.lower() in j_bot.lower():
                is_player = True
                break
                
        target_type = "Ally" if is_player else "Player"
        
        analyzed_targets.append({
            "id": agent.get("id"),
            "name": a_name,
            "type": target_type,
            "hp": target_hp,
            "region_id": r_id,
            "distance": dist,
            "damage_dealt": damage_dealt,
            "damage_received": damage_received,
            "is_in_range": is_in_range,
            "can_one_shot": can_one_shot,
            "priority_score": 0
        })
        
    visible_monsters = view_data.get("visibleMonsters") or []
    for monster in visible_monsters:
        if not isinstance(monster, dict):
            continue
            
        m_name = monster.get("name") or monster.get("displayName") or ""
        
        is_alive = monster.get("isAlive")
        if is_alive is None:
            is_alive = monster.get("is_alive", True)
        hp = monster.get("hp")
        if is_alive is False or (hp is not None and hp <= 0):
            continue
            
        r_id = (
            monster.get("regionId") or 
            monster.get("region_id") or 
            monster.get("currentRegionId") or 
            monster.get("currentRegion", {}).get("id")
        )
        
        dist = distances.get(r_id)
        if dist is None:
            continue
            
        m_type = "wolf"
        name_lower = m_name.lower()
        if "wolf" in name_lower:
            m_type = "wolf"
        elif "bear" in name_lower:
            m_type = "bear"
        elif "bandit" in name_lower:
            m_type = "bandit"
        elif "guardian" in name_lower:
            m_type = "guardian"
            
        monster_stats = MONSTERS.get(m_type, MONSTERS["wolf"])
        target_def = monster_stats.get("def", 1)
        target_atk = monster_stats.get("atk", 10)
        target_hp = monster.get("hp", monster_stats.get("hp", 25))
        
        damage_dealt = max(1, our_total_atk - target_def)
        damage_received = max(1, target_atk - our_total_def)
        
        is_in_range = dist <= our_weapon_range
        can_one_shot = target_hp <= damage_dealt
        
        m_id = monster.get("id") or monster.get("instanceId") or monster.get("instance_id") or m_name
        
        analyzed_targets.append({
            "id": m_id,
            "name": m_name,
            "type": "Guardian" if m_type == "guardian" else "Monster",
            "hp": target_hp,
            "region_id": r_id,
            "distance": dist,
            "damage_dealt": damage_dealt,
            "damage_received": damage_received,
            "is_in_range": is_in_range,
            "can_one_shot": can_one_shot,
            "priority_score": 0
        })

    for target in analyzed_targets:
        score = 0
        if target["can_one_shot"]:
            score += 1000
        if target["is_in_range"]:
            score += 500
        else:
            score -= (target["distance"] * 100)
            
        score += (150 - target["hp"])
        score += (target["damage_dealt"] * 10)
        score -= (target["damage_received"] * 5)
        
        if target["type"] in ("Player", "Ally"):
            score += 200
        elif target["type"] == "Guardian":
            score -= 100
            
        target["priority_score"] = score

    analyzed_targets.sort(key=lambda x: x["priority_score"], reverse=True)
    
    best_target = None
    action_recommendation = "none"
    can_attack = False
    
    if analyzed_targets:
        top_target = analyzed_targets[0]
        if top_target["is_in_range"] and our_ep >= our_weapon_ep_cost:
            can_attack = True
            best_target = top_target
            action_recommendation = "attack"
        else:
            best_target = top_target
            action_recommendation = "move_closer" if our_hp >= 40 else "retreat"
            
    return {
        "can_attack": can_attack,
        "best_target": best_target,
        "action_recommendation": action_recommendation,
        "targets_in_range": [t for t in analyzed_targets if t["is_in_range"]],
        "all_visible_targets": analyzed_targets
    }