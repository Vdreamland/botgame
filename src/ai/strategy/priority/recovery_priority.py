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
        
        current_region_id = view.get("currentRegion", {}).get("id")
        visible_agents = view.get("visibleAgents", [])
        visible_monsters = view.get("visibleMonsters", [])
        my_id = self_data.get("id")
        
        has_nearby_enemies = False
        for agent in visible_agents:
            if agent.get("id") != my_id and agent.get("isAlive", True):
                has_nearby_enemies = True
                break
        if not has_nearby_enemies:
            for monster in visible_monsters:
                if monster.get("isAlive", True):
                    has_nearby_enemies = True
                    break
                    
        has_layer_0_enemies = False
        for agent in visible_agents:
            if agent.get("id") != my_id and agent.get("regionId") == current_region_id and agent.get("isAlive", True):
                has_layer_0_enemies = True
                break
        if not has_layer_0_enemies:
            for monster in visible_monsters:
                if monster.get("regionId") == current_region_id and monster.get("isAlive", True):
                    has_layer_0_enemies = True
                    break
                    
        if not has_layer_0_enemies and has_nearby_enemies:
            if hp < 90:
                for item in inventory:
                    name = item.get("name")
                    item_id = item.get("id")
                    if name in RECOVERY_ITEMS and RECOVERY_ITEMS[name].get("hp_heal", 0) > 0:
                        return 74, {"action_type": "use_item", "item_id": item_id}
            if ep < 7:
                for item in inventory:
                    name = item.get("name")
                    item_id = item.get("id")
                    if name in RECOVERY_ITEMS and RECOVERY_ITEMS[name].get("ep_heal", 0) > 0:
                        return 74, {"action_type": "use_item", "item_id": item_id}
                return 74, {"action_type": "rest"}
        
        if not has_nearby_enemies and ep < 8:
            for item in inventory:
                name = item.get("name")
                item_id = item.get("id")
                if name in RECOVERY_ITEMS and RECOVERY_ITEMS[name].get("ep_heal", 0) > 0:
                    return 65, {"action_type": "use_item", "item_id": item_id}
            return 60, {"action_type": "rest"}
        
        return 0, None