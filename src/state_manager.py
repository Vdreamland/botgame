import json
from src.game_log import print_turn_log
from src.ai.detector.self_detector import parse_self_status
from src.ai.detector.loot_detector import parse_loot_status
from src.ai.detector.zone_detector import parse_zone_status
from src.ai.detector.radar_detector import parse_radar_status
from src.ai.detector.enemy_detector import parse_enemy_status
from src.ai.detector.deadzone_detector import parse_deadzone_status
from src.utils.zone_helper import calculate_region_distances
from src.agent_memory import AgentMemory
from src.combat_handler import process_combat_message

class StateManager:
    def __init__(self):
        self.current_turn = 1
        self.alive_count = 0
        self.known_entities = {}
        self.fight_history = []
        self.region_name_map = {}
        self.current_distances = {}
        self.memory = AgentMemory()
        self.pending_loot_regions = self.memory.pending_loot_regions
        self.interacted_facilities = self.memory.interacted_facilities
        self.searched_regions = set()
        self.last_visited_region_id = None
        self.can_act = True
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

    def process_message(self, frame_type, data):
        if frame_type in ["agent_view", "turn_advanced", "can_act_changed"]:
            view_data = data.get("view", {})
            self._update_entities(view_data)
        
            prev_hp = self.status.get("hp", 0)
            prev_region_id = self.status.get("region_id")
            prev_history_len = len(self.fight_history)
        
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
        
            if current_region_id in self.pending_loot_regions:
                self.pending_loot_regions.remove(current_region_id)
        
            self.current_distances = calculate_region_distances(current_region, visible_regions)
        
            self.status = parse_self_status(data)
        
            curr_region_id = self.status.get("region_id")
            if prev_region_id and curr_region_id != prev_region_id:
                self.last_visited_region_id = prev_region_id
        
            self.zone_status = parse_zone_status(data)
            self.loot_status = parse_loot_status(data)
            self.radar_status = parse_radar_status(data, self.current_distances)
            self.enemy_status = parse_enemy_status(data, self.known_entities, self.current_distances)
            self.deadzone_status = parse_deadzone_status(data, self.current_distances)
        
            self.current_turn = data.get("turn", self.current_turn)
            self.alive_count = view_data.get("aliveCount", self.alive_count)
            self.can_act = data.get("canAct", self.can_act)
        
            curr_hp = self.status.get("hp", 0)
            if curr_hp < prev_hp and prev_hp > 0 and len(self.fight_history) == prev_history_len:
                damage_taken = prev_hp - curr_hp
                layer_0 = self.enemy_status.get("layers", {}).get(0, {})
                possible_attackers = []
                for agent in layer_0.get("agents", []):
                    possible_attackers.append(agent.get("name"))
                for monster in layer_0.get("monsters", []):
                    possible_attackers.append(monster.get("name"))
        
                region_name = self.zone_status.get("location", "Unknown Region")
                if possible_attackers:
                    attacker_name = possible_attackers[0] if len(possible_attackers) == 1 else ", ".join(possible_attackers)
                    log_msg = f"{attacker_name} attacked You for {damage_taken} damage using None from {region_name} (Same Region)"
                else:
                    log_msg = f"You took {damage_taken} damage from an unknown source or environment in {region_name}"
        
                self.fight_history.append(log_msg)
                if len(self.fight_history) > 10:
                    self.fight_history.pop(0)
        
            eq_weapon = self.status.get("equipped_weapon")
            eq_weapon_name = eq_weapon.get("name") if isinstance(eq_weapon, dict) else (eq_weapon if eq_weapon else "None")
            
            self.memory.update_my_state(
                bot_name=self.status.get("name", "Unknown"),
                hp=self.status.get("hp", 0),
                ep=self.status.get("ep", 0),
                region_id=self.status.get("region_id"),
                weapon=eq_weapon_name,
                target_id=None,
                inventory=self.status.get("inventory", [])
            )
        
            if frame_type == "turn_advanced":
                print_turn_log(self.current_turn, self.status, self.zone_status, self.loot_status, self.radar_status, self.enemy_status, self.alive_count, fight_history=self.fight_history, deadzone_status=self.deadzone_status, pending_loot_regions=self.pending_loot_regions, interacted_facilities=list(self.interacted_facilities))
        
        else:
            process_combat_message(self, frame_type, data)

    def is_agent_dead(self):
        return self.status["hp"] == 0 or not self.status["is_alive"]