import json
from src.game_log import print_turn_log
from src.ai.detector.self_detector import parse_self_status
from src.ai.detector.loot_detector import parse_loot_status
from src.ai.detector.zone_detector import parse_zone_status
from src.ai.detector.radar_detector import parse_radar_status
from src.ai.detector.enemy_detector import parse_enemy_status
from src.ai.detector.deadzone_detector import parse_deadzone_status
from src.utils.zone_helper import calculate_region_distances

class StateManager:
    def __init__(self):
        self.current_turn = 1
        self.alive_count = 0
        self.known_entities = {}
        self.fight_history = []
        self.region_name_map = {}
        self.current_distances = {}
        self.status = {
            "name": "Unknown",
            "hp": 0,
            "max_hp": 0,
            "ep": 0,
            "max_ep": 0,
            "is_alive": True,
            "region_id": None,
            "location": "Unknown",
            "atk": 0,
            "def": 0,
            "kills": 0,
            "vision": 0,
            "has_weapon": False,
            "equipped_weapon": None,
            "has_armor": False,
            "equipped_armor": None,
            "inventory": []
        }
        self.zone_status = {
            "location": "Unknown",
            "terrain": "plains",
            "weather": "clear",
            "vision_modifier": 0,
            "facilities": [],
            "links_count": 0
        }
        self.loot_status = {
            "ground_items": [],
            "ground_item_count": 0
        }
        self.radar_status = {
            "layers": {},
            "max_detected_layer": 0
        }
        self.enemy_status = {
            "layers": {i: {"counts": {"P": 0, "M": 0, "A": 0}, "agents": [], "monsters": []} for i in range(4)}
        }
        self.deadzone_status = {
            "current_region_status": "Safe",
            "active_deadzones": [],
            "pending_deadzones": []
        }

    def _update_entities(self, view_data):
        self_id = view_data.get("self", {}).get("id")
        if self_id:
            self.my_id = self_id
            
        for agent in view_data.get("visibleAgents", []):
            agent_id = agent.get("id")
            if agent_id:
                agent["entity_type"] = "agent"
                self.known_entities[agent_id] = agent
                
        if self_id and self_id not in self.known_entities:
            self_agent = view_data.get("self", {})
            self_agent["entity_type"] = "agent"
            self.known_entities[self_id] = self_agent

        for monster in view_data.get("visibleMonsters", []):
            monster_id = monster.get("id")
            if monster_id:
                monster["entity_type"] = "monster"
                self.known_entities[monster_id] = monster
                
        for npc in view_data.get("visibleNPCs", []):
            npc_id = npc.get("id")
            if npc_id:
                npc["entity_type"] = "npc"
                self.known_entities[npc_id] = npc

    def process_message(self, frame_type, data):
        if frame_type in ["agent_view", "turn_advanced"]:
            view_data = data.get("view", {})
            self._update_entities(view_data)
            
            visible_regions = view_data.get("visibleRegions", [])
            for r in visible_regions:
                r_id = r.get("id")
                r_name = r.get("name")
                if r_id and r_name:
                    self.region_name_map[r_id] = r_name
                    
            current_region = view_data.get("currentRegion", {})
            current_region_id = current_region.get("id")
            if current_region_id and current_region.get("name"):
                self.region_name_map[current_region_id] = current_region.get("name")
                
            self.current_distances = calculate_region_distances(current_region, visible_regions)
            
            self.status = parse_self_status(data)
            self.zone_status = parse_zone_status(data)
            self.loot_status = parse_loot_status(data)
            self.radar_status = parse_radar_status(data, self.current_distances)
            self.enemy_status = parse_enemy_status(data, self.known_entities, self.current_distances)
            self.deadzone_status = parse_deadzone_status(data, self.current_distances)
            
            self.current_turn = data.get("turn", self.current_turn)
            self.alive_count = view_data.get("aliveCount", self.alive_count)
            
            print_turn_log(self.current_turn, self.status, self.zone_status, self.loot_status, self.radar_status, self.enemy_status, self.alive_count, fight_history=self.fight_history, deadzone_status=self.deadzone_status)
            
        elif frame_type in ["hp_changed", "agent_damaged", "monster_damaged"]:
            target_id = data.get("targetId")
            attacker_id = data.get("agentId", data.get("attackerId"))
            damage = data.get("damage", 0)
            
            entity_id = target_id if target_id else attacker_id
            if entity_id and entity_id in self.known_entities:
                self.known_entities[entity_id]["hp"] = data.get("hp", data.get("currentHp", 0))
                
            if hasattr(self, "my_id") and entity_id == self.my_id:
                new_hp = data.get("hp", data.get("currentHp", 0))
                self.status["hp"] = new_hp
                if new_hp == 0:
                    self.status["is_alive"] = False
                    
            if target_id and attacker_id and damage > 0:
                is_target_me = hasattr(self, "my_id") and target_id == self.my_id
                is_attacker_me = hasattr(self, "my_id") and attacker_id == self.my_id
                
                if is_target_me or is_attacker_me:
                    attacker_data = self.known_entities.get(attacker_id, {})
                    target_data = self.known_entities.get(target_id, {})
                    
                    attacker_name = attacker_data.get("name", "Unknown") if not is_attacker_me else "You"
                    target_name = target_data.get("name", "Unknown") if not is_target_me else "You"
                    
                    if not is_attacker_me and not attacker_data:
                        attacker_name = data.get("agentName", data.get("attackerName", "Unknown"))
                        
                    weapon_val = data.get("weapon")
                    if not weapon_val:
                        weapon_val = attacker_data.get("equippedWeapon", "None")
                    
                    weapon_name = "None"
                    if isinstance(weapon_val, dict):
                        weapon_name = weapon_val.get("name", "None")
                    elif isinstance(weapon_val, str):
                        weapon_name = weapon_val
                        
                    region_id = target_data.get("regionId", target_data.get("region_id"))
                    if not region_id:
                        region_id = attacker_data.get("regionId", attacker_data.get("region_id"))
                    if not region_id and hasattr(self, "status"):
                        region_id = self.status.get("region_id")
                        
                    region_name = self.region_name_map.get(region_id, "Unknown Region")
                    
                    dist = self.current_distances.get(region_id)
                    layer_str = f"Layer {dist}" if dist is not None else "Unknown Layer"
                    if dist == 0:
                        layer_str = "Same Region"
                        
                    if is_target_me:
                        log_msg = f"{attacker_name} attacked You for {damage} damage using {weapon_name} from {region_name} ({layer_str})"
                    else:
                        log_msg = f"You attacked {target_name} for {damage} damage using {weapon_name} in {region_name} ({layer_str})"
                        
                    self.fight_history.append(log_msg)
                    if len(self.fight_history) > 10:
                        self.fight_history.pop(0)
                        
        elif frame_type in ["agent_died", "monster_killed"]:
            entity_id = data.get("targetId", data.get("agentId"))
            if entity_id and entity_id in self.known_entities:
                self.known_entities[entity_id]["hp"] = 0
                self.known_entities[entity_id]["isAlive"] = False
                
            if hasattr(self, "my_id") and entity_id == self.my_id:
                self.status["hp"] = 0
                self.status["is_alive"] = False
                
        elif frame_type == "ep_changed":
            entity_id = data.get("targetId", data.get("agentId"))
            new_ep = data.get("ep", data.get("currentEp", 0))
            if hasattr(self, "my_id") and entity_id == self.my_id:
                self.status["ep"] = new_ep

    def is_agent_dead(self):
        return self.status["hp"] == 0 or not self.status["is_alive"]