import os
from src.game_data import MONSTERS, GUARDIANS, WEAPONS

def get_ally_names(my_name):
 allies = set()
 for key, value in os.environ.items():
  if key.startswith("BOT") and key.endswith("_NAME"):
   if value and value != my_name:
    allies.add(value)
 return allies

class SurvivalPriority:
 def evaluate(self, manager, raw_data):
  view = raw_data.get("view", {})
  self_data = view.get("self", {})
  my_id = self_data.get("id")
  my_name = self_data.get("name", "Unknown")
  current_region_id = view.get("currentRegion", {}).get("id")
  
  if not current_region_id:
   return 0, None
  
  hp = self_data.get("hp", 100)
  max_hp = self_data.get("maxHp", 100)
  hp_ratio = hp / max_hp if max_hp > 0 else 1.0
  
  my_atk = self_data.get("atk", 25)
  my_def = self_data.get("def", 7)
  
  equipped_weapon = self_data.get("equippedWeapon")
  eq_weapon_name = equipped_weapon.get("name") if isinstance(equipped_weapon, dict) else (equipped_weapon if equipped_weapon else "None")
  has_weapon = (eq_weapon_name not in ["None", "Fist"])
  
  visible_agents = view.get("visibleAgents", [])
  visible_monsters = view.get("visibleMonsters", [])
  
  ally_names = get_ally_names(my_name)
  
  visible_regions = view.get("visibleRegions", [])
  my_region_data = next((r for r in visible_regions if r.get("id") == current_region_id), {})
  if not my_region_data:
   my_region_data = view.get("currentRegion", {})
  ground_items = my_region_data.get("items", []) if my_region_data else []
  
  has_ground_weapon = False
  if ground_items:
   for item in ground_items:
    name = item.get("name") if isinstance(item, dict) else item
    if name in WEAPONS and name not in ["None", "Fist"]:
     has_ground_weapon = True
     break
  
  has_dangerous_enemies = False
  unarmed_danger = False
  has_layer_0_enemies = False
  
  for agent in visible_agents:
   if agent.get("id") != my_id:
    agent_name = agent.get("name", "")
    if agent_name in ally_names:
     continue
    
    region_id = agent.get("regionId")
    if region_id == current_region_id:
     if agent.get("isAlive", True):
      has_layer_0_enemies = True
      is_guard = (agent.get("isGuardian") or "guardian" in agent_name.lower())
      
      target_hp = agent.get("hp", 100)
      target_atk = agent.get("atk") if agent.get("atk") is not None else 25
      target_def = agent.get("def") if agent.get("def") is not None else 5
      
      my_dmg = max(1, my_atk - target_def)
      target_dmg = max(1, target_atk - my_def)
      
      turns_to_kill_enemy = (target_hp + my_dmg - 1) // my_dmg
      turns_to_kill_me = (hp + target_dmg - 1) // target_dmg
      
      if hp < 30 and target_hp > 30:
       is_combat_feasible = False
      else:
       is_combat_feasible = (turns_to_kill_enemy < turns_to_kill_me) or (turns_to_kill_enemy <= 2) or (target_hp <= 40)
      
      if not is_combat_feasible:
       has_dangerous_enemies = True
      
      enemy_weapon = agent.get("equippedWeapon")
      enemy_weapon = enemy_weapon.get("name") if isinstance(enemy_weapon, dict) else (enemy_weapon if enemy_weapon else "None")
      enemy_has_weapon = (enemy_weapon not in ["None", "Fist"])
      
      if not has_weapon and enemy_has_weapon and not has_ground_weapon:
       unarmed_danger = True
  
  for monster in visible_monsters:
   region_id = monster.get("regionId")
   if region_id == current_region_id:
    if monster.get("isAlive", True):
     has_layer_0_enemies = True
     monster_name = monster.get("name", "")
     is_guard = ("guardian" in monster_name.lower() or monster.get("maxHp", 100) >= 50)
     
     if is_guard:
      base_stats = {"atk": 12, "def": 150}
     else:
      base_stats = MONSTERS.get(monster_name, {"atk": 25, "def": 5})
     
     target_hp = monster.get("hp", 100)
     target_atk = monster.get("atk") if monster.get("atk") is not None else base_stats.get("atk", 25)
     target_def = monster.get("def") if monster.get("def") is not None else base_stats.get("def", 5)
     
     my_dmg = max(1, my_atk - target_def)
     target_dmg = max(1, target_atk - my_def)
     
     turns_to_kill_enemy = (target_hp + my_dmg - 1) // my_dmg
     turns_to_kill_me = (hp + target_dmg - 1) // target_dmg
     
     is_combat_feasible = (turns_to_kill_enemy < turns_to_kill_me) or (turns_to_kill_enemy <= 2) or (target_hp <= 40)
     if not is_combat_feasible:
      has_dangerous_enemies = True
     
     if not has_weapon and not has_ground_weapon:
      if is_guard or hp < 50:
       unarmed_danger = True
  
  if hp_ratio < 0.4 and has_layer_0_enemies:
   if has_dangerous_enemies:
    return 97, {"action_type": "flee"}
  
  if unarmed_danger:
   return 92, {"action_type": "flee"}
  
  return 0, None