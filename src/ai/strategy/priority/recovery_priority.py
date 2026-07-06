from src.game_data import RECOVERY_ITEMS, UTILITY_ITEMS

class RecoveryPriority:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        self_data = view.get("self", {})
        hp = self_data.get("hp", 100)
        max_hp = self_data.get("maxHp", 100)
        ep = self_data.get("ep", 10)
        current_turn = manager.current_turn if hasattr(manager, "current_turn") else 1
        
        inventory = self_data.get("inventory", [])
        
        for item in inventory:
            name = item.get("name")
            item_id = item.get("id")
            if name in UTILITY_ITEMS:
                server_use_type = item.get("useType", "active")
                static_use_type = UTILITY_ITEMS[name].get("use_type", "active")
                if server_use_type != "passive" and static_use_type == "active":
                    return 100, {"action_type": "use_item", "item_id": item_id}
        
        hp_ratio = hp / max_hp if max_hp > 0 else 1.0
        
        if hp_ratio < 0.4:
            for item in inventory:
                name = item.get("name")
                item_id = item.get("id")
                if name in RECOVERY_ITEMS and RECOVERY_ITEMS[name].get("hp_heal", 0) > 0:
                    return 99, {"action_type": "use_item", "item_id": item_id}
                    
        if current_turn >= 58 and hp < max_hp:
            for item in inventory:
                name = item.get("name")
                item_id = item.get("id")
                if name in RECOVERY_ITEMS and RECOVERY_ITEMS[name].get("hp_heal", 0) > 0:
                    return 100, {"action_type": "use_item", "item_id": item_id}
                    
        if hp_ratio < 0.7:
            for item in inventory:
                name = item.get("name")
                item_id = item.get("id")
                if name in RECOVERY_ITEMS and RECOVERY_ITEMS[name].get("hp_heal", 0) > 0:
                    return 96, {"action_type": "use_item", "item_id": item_id}
                    
        if ep < 3:
            for item in inventory:
                name = item.get("name")
                item_id = item.get("id")
                if name in RECOVERY_ITEMS and RECOVERY_ITEMS[name].get("ep_heal", 0) > 0:
                    return 75, {"action_type": "use_item", "item_id": item_id}
            return 70, {"action_type": "rest"}
            
        return 0, None