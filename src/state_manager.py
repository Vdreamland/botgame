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

    def _update_entities(self, view_data):
        self_id = view_data.get("self", {}).get("id")
        
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
            
            self.current_turn = data.get("turn", self.current_turn)
            self.alive_count = view_data.get("aliveCount", self.alive_count)
            
        elif frame_type == "turn_advanced":
            self.current_turn = data.get("turn", self.current_turn + 1)
            self.alive_count = data.get("aliveCount", self.alive_count)
            
        elif frame_type in ["hp_changed", "agent_damaged", "monster_damaged"]:
            entity_id = data.get("targetId", data.get("agentId"))
            if entity_id and entity_id in self.known_entities:
                self.known_entities[entity_id]["hp"] = data.get("hp", data.get("currentHp", 0))

        elif frame_type in ["agent_died", "monster_killed"]:
             entity_id = data.get("targetId", data.get("agentId"))
             if entity_id and entity_id in self.known_entities:
                self.known_entities[entity_id]["hp"] = 0
                self.known_entities[entity_id]["isAlive"] = False

        elif frame_type in ["agent_moved", "monster_moved"]:
            entity_id = data.get("agentId", data.get("targetId", data.get("monsterId")))
            new_region_id = data.get("regionId", data.get("region_id", data.get("toRegionId")))
            if entity_id and new_region_id and entity_id in self.known_entities:
                self.known_entities[entity_id]["regionId"] = new_region_id
        
        if frame_type in ["agent_view", "turn_advanced"]:
            status = parse_self_status(data)
            zone_status = parse_zone_status(data)
            loot_status = parse_loot_status(data)
            radar_status = parse_radar_status(data)
            enemy_status = parse_enemy_status(data, self.known_entities)
            
            print_turn_log(self.current_turn, status, zone_status, loot_status, radar_status, enemy_status, self.alive_count)

    def is_agent_dead(self, data):
        status = parse_self_status(data)
        return status["hp"] == 0 or not status["is_alive"]