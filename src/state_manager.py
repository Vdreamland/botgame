import json
from src.game_log import print_turn_log
from src.ai.detector.self_detector import parse_self_status
from src.ai.detector.loot_detector import parse_loot_status
from src.ai.detector.zone_detector import parse_zone_status
from src.ai.detector.radar_detector import parse_radar_status
from src.ai.detector.enemy_detector import parse_enemy_status

class StateManager:
    def __init__(self):
        self.current_turn = 1
        self.alive_count = 0
        self.known_entities = {}
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
        if frame_type == "agent_view":
            view_data = data.get("view", {})
            self._update_entities(view_data)
            
            self.status = parse_self_status(data)
            self.zone_status = parse_zone_status(data)
            self.loot_status = parse_loot_status(data)
            self.radar_status = parse_radar_status(data)
            self.enemy_status = parse_enemy_status(data, self.known_entities)
            
            self.current_turn = data.get("turn", self.current_turn)
            self.alive_count = view_data.get("aliveCount", self.alive_count)
            
            print_turn_log(self.current_turn, self.status, self.zone_status, self.loot_status, self.radar_status, self.enemy_status, self.alive_count)
            
        elif frame_type == "turn_advanced":
            self.current_turn = data.get("turn", self.current_turn + 1)
            self.alive_count = data.get("aliveCount", self.alive_count)
            
            print_turn_log(self.current_turn, self.status, self.zone_status, self.loot_status, self.radar_status, self.enemy_status, self.alive_count)
            
        elif frame_type in ["hp_changed", "agent_damaged", "monster_damaged"]:
            entity_id = data.get("targetId", data.get("agentId"))
            if entity_id and entity_id in self.known_entities:
                self.known_entities[entity_id]["hp"] = data.get("hp", data.get("currentHp", 0))
            
            if hasattr(self, "my_id") and entity_id == self.my_id:
                new_hp = data.get("hp", data.get("currentHp", 0))
                self.status["hp"] = new_hp
                if new_hp == 0:
                    self.status["is_alive"] = False
                    print_turn_log(self.current_turn, self.status, self.zone_status, self.loot_status, self.radar_status, self.enemy_status, self.alive_count)
                
        elif frame_type in ["agent_died", "monster_killed"]:
            entity_id = data.get("targetId", data.get("agentId"))
            if entity_id and entity_id in self.known_entities:
                self.known_entities[entity_id]["hp"] = 0
                self.known_entities[entity_id]["isAlive"] = False
                
            if hasattr(self, "my_id") and entity_id == self.my_id:
                self.status["hp"] = 0
                self.status["is_alive"] = False
                print_turn_log(self.current_turn, self.status, self.zone_status, self.loot_status, self.radar_status, self.enemy_status, self.alive_count)
                
        elif frame_type == "ep_changed":
            entity_id = data.get("targetId", data.get("agentId"))
            new_ep = data.get("ep", data.get("currentEp", 0))
            if hasattr(self, "my_id") and entity_id == self.my_id:
                self.status["ep"] = new_ep

    def is_agent_dead(self):
        return self.status["hp"] == 0 or not self.status["is_alive"]