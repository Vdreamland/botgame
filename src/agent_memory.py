import json
import os
import time

class AgentMemory:
    def __init__(self):
        self.interacted_facilities = set()
        self.pending_loot_regions = []
        self.visited_history = []
        self.shared_file = "shared_team_memory.json"

    def reset_local(self):
        self.interacted_facilities.clear()
        self.pending_loot_regions.clear()
        self.visited_history.clear()

    def reset_shared(self):
        for _ in range(5):
            try:
                if os.path.exists(self.shared_file):
                    mtime = os.path.getmtime(self.shared_file)
                    if time.time() - mtime > 15:
                        os.remove(self.shared_file)
                break
            except Exception:
                time.sleep(0.05)

    def add_visited_region(self, region_id):
        if not region_id:
            return
        if region_id in self.visited_history:
            self.visited_history.remove(region_id)
        self.visited_history.append(region_id)
        if len(self.visited_history) > 5:
            self.visited_history.pop(0)

    def update_my_state(self, bot_name, hp, ep, region_id, weapon, target_id, inventory):
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
                    "target_id": target_id,
                    "inventory": inventory,
                    "timestamp": time.time()
                }
                
                with open(self.shared_file, "w") as f:
                    json.dump(data, f)
                break
            except Exception:
                time.sleep(0.05)

    def get_team_states(self):
        for _ in range(5):
            try:
                if os.path.exists(self.shared_file):
                    with open(self.shared_file, "r") as f:
                        return json.load(f)
                return {}
            except Exception:
                time.sleep(0.05)
        return {}