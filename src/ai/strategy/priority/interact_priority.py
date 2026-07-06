class InteractPriority:
    def evaluate(self, manager, raw_data):
        view = raw_data.get("view", {})
        self_data = view.get("self", {})
        hp = self_data.get("hp", 100)
        max_hp = self_data.get("maxHp", 100)
        inventory = view.get("inventory", [])
        
        current_region = view.get("currentRegion", {})
        interactables = current_region.get("interactables", [])
        if not interactables:
            return 0, None
            
        for facility in interactables:
            name = facility.get("name")
            facility_id = facility.get("id")
            if not name:
                continue
                
            if name == "Medical Facility" and (hp / max_hp if max_hp > 0 else 1.0) < 0.7:
                return 87, {"action_type": "interact", "facility_id": facility_id or name}
                
            if name == "Supply Cache" and len(inventory) < 10:
                return 83, {"action_type": "interact", "facility_id": facility_id or name}
                
            if name == "Watchtower":
                return 45, {"action_type": "interact", "facility_id": facility_id or name}
                
        return 0, None