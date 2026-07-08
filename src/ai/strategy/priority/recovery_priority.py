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
        
        recovery_lower = {k.lower(): v for k, v in RECOVERY_ITEMS.items()}
        
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
                name_lower = name.lower() if name else ""
                if name_lower in recovery_lower and recovery_lower[name_lower].get("hp_heal", 0) > 0:
                    return 99, {"action_type": "use_item", "item_id": item_id}
        
        if current_turn >= 58 and hp < max_hp:
            for item in inventory:
                name = item.get("name")
                item_id = item.get("id")
                name_lower = name.lower() if name else ""
                if name_lower in recovery_lower and recovery_lower[name_lower].get("hp_heal", 0) > 0:
                    return 100, {"action_type": "use_item", "item_id": item_id}
        
        if hp_ratio < 0.7:
            for item in inventory:
                name = item.get("name")
                item_id = item.get("id")
                name_lower = name.lower() if name else ""
                if name_lower in recovery_lower and recovery_lower[name_lower].get("hp_heal", 0) > 0:
                    return 96, {"action_type": "use_item", "item_id": item_id}
        
        has_layer_0_enemies = getattr(manager, "has_layer_0_enemies", False)
        has_nearby_enemies = getattr(manager, "has_nearby_enemies", False)
        
        if not has_layer_0_enemies:
            if ep < 5:
                target_score = 95 if has_nearby_enemies else 70
                for item in inventory:
                    name = item.get("name")
                    item_id = item.get("id")
                    name_lower = name.lower() if name else ""
                    if name_lower in recovery_lower and recovery_lower[name_lower].get("ep_heal", 0) > 0:
                        return target_score + 1, {"action_type": "use_item", "item_id": item_id}
                return target_score, {"action_type": "rest"}
        
        if not has_layer_0_enemies and has_nearby_enemies:
            if hp < 90:
                for item in inventory:
                    name = item.get("name")
                    item_id = item.get("id")
                    name_lower = name.lower() if name else ""
                    if name_lower in recovery_lower and recovery_lower[name_lower].get("hp_heal", 0) > 0:
                        return 74, {"action_type": "use_item", "item_id": item_id}
            if ep < 7:
                for item in inventory:
                    name = item.get("name")
                    item_id = item.get("id")
                    name_lower = name.lower() if name else ""
                    if name_lower in recovery_lower and recovery_lower[name_lower].get("ep_heal", 0) > 0:
                        score = 74 if ep < 3 else 48
                        return score, {"action_type": "use_item", "item_id": item_id}
                score = 74 if ep < 3 else 48
                return score, {"action_type": "rest"}
        
        if not has_nearby_enemies and ep < 8:
            for item in inventory:
                name = item.get("name")
                item_id = item.get("id")
                name_lower = name.lower() if name else ""
                if name_lower in recovery_lower and recovery_lower[name_lower].get("ep_heal", 0) > 0:
                    score = 65 if ep < 3 else 45
                    return score, {"action_type": "use_item", "item_id": item_id}
            score = 60 if ep < 3 else 45
            return score, {"action_type": "rest"}
        
        return 0, None