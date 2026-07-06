from src.game_data import WEAPONS, ARMOR, RECOVERY_ITEMS

class GroundLootPriority:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        self_data = view.get("self", {})
        inventory = view.get("inventory", [])
        
        if len(inventory) >= 10:
            return 0, None
            
        current_region = view.get("currentRegion", {})
        ground_items = current_region.get("visibleItems", [])
        if not ground_items:
            return 0, None
            
        for item in ground_items:
            name = item.get("name")
            item_id = item.get("id")
            if not name or not item_id:
                continue
                
            if name == "sMoltz":
                return 82, {"action_type": "loot", "item_id": item_id}
                
            if name in WEAPONS or name in ARMOR:
                return 78, {"action_type": "loot", "item_id": item_id}
                
            if name in RECOVERY_ITEMS:
                return 72, {"action_type": "loot", "item_id": item_id}
                
            return 60, {"action_type": "loot", "item_id": item_id}
            
        return 0, None