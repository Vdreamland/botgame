import json
import os
import time

class AgentMemory:
    def __init__(self, shared_file="shared_team_memory.json"):
        self.shared_file = shared_file
        self.visited_history = []
        self.interacted_facilities = set()
        self.pending_loot_regions = []
        self.reset_local()

    def reset_local(self):
        self.visited_history = []
        self.interacted_facilities.clear()
        self.pending_loot_regions = []

    def reset_shared(self):
        for _ in range(5):
            try:
                with open(self.shared_file, "w") as f:
                    json.dump({}, f)
                break
            except Exception:
                time.sleep(0.05)

    def add_visited_region(self, region_id):
        if not region_id:
            return
        if region_id in self.visited_history:
            self.visited_history.remove(region_id)
        self.visited_history.append(region_id)
        if len(self.visited_history) > 10:
            self.visited_history.pop(0)

    def update_my_state(self, bot_name, hp, ep, region_id, weapon, target_id, inventory, game_id=None, armor=None):
        if not bot_name:
            return
        for _ in range(5):
            try:
                data = {}
                if os.path.exists(self.shared_file):
                    with open(self.shared_file, "r") as f:
                        data = json.load(f)
                
                data[bot_name] = {
                    "hp": hp,
                    "ep": ep,
                    "region_id": region_id,
                    "weapon": weapon,
                    "armor": armor,
                    "target_id": target_id,
                    "inventory": inventory,
                    "timestamp": time.time(),
                    "game_id": game_id
                }
                
                with open(self.shared_file, "w") as f:
                    json.dump(data, f)
                break
            except Exception:
                time.sleep(0.05)

    def get_team_states(self, current_game_id=None):
        data = self._read_shared_memory()
        if not data:
            return {}
        
        valid_states = {}
        now = time.time()
        for name, state in data.items():
            timestamp = state.get("timestamp", 0)
            if now - timestamp < 15.0:
                if current_game_id is None or state.get("game_id") == current_game_id:
                    valid_states[name] = state
        return valid_states

    def _read_shared_memory(self):
        try:
            if os.path.exists(self.shared_file):
                with open(self.shared_file, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}