class InteractPriority:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        self_data = view.get("self", {})
        hp = self_data.get("hp", 100)
        max_hp = self_data.get("maxHp", 100)
        inventory = self_data.get("inventory", [])
        
        current_region = view.get("currentRegion", {})
        current_region_id = current_region.get("id")
        interactables = current_region.get("interactables", [])
        
        if not current_region_id or not interactables:
            return 0, None
            
        for facility in interactables:
            name = facility.get("name")
            facility_id = facility.get("id")
            if not name:
                continue
                
            if name not in ["Supply Cache", "Medical Facility", "Watchtower"]:
                continue
                
            facility_key = f"{current_region_id}_{name}"
            if hasattr(manager, "interacted_facilities") and facility_key in manager.interacted_facilities:
                continue
                
            if name == "Medical Facility" and (hp / max_hp if max_hp > 0 else 1.0) < 0.7:
                return 96, {"action_type": "interact", "facility_id": facility_id or name, "facility_name": name}
                
            if name == "Supply Cache" and len(inventory) < 10:
                return 83, {"action_type": "interact", "facility_id": facility_id or name, "facility_name": name}
                
            if name == "Watchtower" and manager.alive_count > 1:
                has_outer_players = False
                enemy_status = getattr(manager, "enemy_status", {})
                for dist, layer_data in enemy_status.get("layers", {}).items():
                    if dist > 0:
                        for agent in layer_data.get("agents", []):
                            has_outer_players = True
                            break
                if has_outer_players:
                    return 45, {"action_type": "interact", "facility_id": facility_id or name, "facility_name": name}
                    
        return 0, None