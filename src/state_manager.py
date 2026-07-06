import json
from src.game_log import print_turn_log
from src.ai.detector.self_detector import parse_self_status
from src.ai.detector.loot_detector import parse_loot_status
from src.ai.detector.zone_detector import parse_zone_status
from src.ai.detector.radar_detector import parse_radar_status

class StateManager:
    def __init__(self):
        self.current_turn = 1
        self.alive_count = 0
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

    def process_message(self, frame_type, data):
        if frame_type == "agent_view":
            view_data = data.get("view", {})
            self.status = parse_self_status(data)
            self.zone_status = parse_zone_status(data)
            self.loot_status = parse_loot_status(data)
            self.radar_status = parse_radar_status(data)
            
            self.current_turn = data.get("turn", self.current_turn)
            self.alive_count = view_data.get("aliveCount", self.alive_count)
            
            print_turn_log(self.current_turn, self.status, self.zone_status, self.loot_status, self.radar_status, self.alive_count)
            
        elif frame_type == "turn_advanced":
            self.current_turn = data.get("turn", self.current_turn + 1)
            self.alive_count = data.get("aliveCount", self.alive_count)
            
            print_turn_log(self.current_turn, self.status, self.zone_status, self.loot_status, self.radar_status, self.alive_count)
            
        elif frame_type == "hp_changed":
            new_hp = data.get("hp", data.get("currentHp", self.status.get("hp", 0)))
            self.status["hp"] = new_hp
            if new_hp == 0:
                self.status["is_alive"] = False
                
        elif frame_type == "ep_changed":
            new_ep = data.get("ep", data.get("currentEp", self.status.get("ep", 0)))
            self.status["ep"] = new_ep

    def is_agent_dead(self):
        return self.status["hp"] == 0 or not self.status["is_alive"]