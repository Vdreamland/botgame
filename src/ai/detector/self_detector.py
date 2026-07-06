def parse_self_status(agent_view_data):
    view = agent_view_data.get("view", {})
    self_data = view.get("self", {})
    
    hp = self_data.get("hp", 0)
    max_hp = self_data.get("maxHp", 100)
    ep = self_data.get("ep", 0)
    max_ep = self_data.get("maxEp", 10)
    
    equipped_weapon = self_data.get("equippedWeapon")
    equipped_armor = self_data.get("equippedArmor")
    inventory = self_data.get("inventory", [])
    
    hp_ratio = hp / max_hp if max_hp > 0 else 0.0
    inventory_list = [item.get("name", "Unknown Item") for item in inventory]
    
    return {
        "name": self_data.get("name", "Unknown"),
        "hp": hp,
        "max_hp": max_hp,
        "hp_ratio": hp_ratio,
        "ep": ep,
        "max_ep": max_ep,
        "is_alive": self_data.get("isAlive", True),
        "region_id": self_data.get("regionId", "Unknown"),
        "has_weapon": equipped_weapon is not None,
        "equipped_weapon": equipped_weapon,
        "has_armor": equipped_armor is not None,
        "equipped_armor": equipped_armor,
        "inventory": inventory_list
    }