RECOVERY_ITEMS = {
    "Emergency Food": {"hp_bonus": 20, "ep_bonus": 0, "ep_cost": 0},
    "Bandage": {"hp_bonus": 10, "ep_bonus": 0, "ep_cost": 0},
    "Medkit": {"hp_bonus": 30, "ep_bonus": 5, "ep_cost": 0},
    "Energy drink": {"hp_bonus": 0, "ep_bonus": 5, "ep_cost": 0}
}

UTILITY_ITEMS = {
    "Megaphone": {"effect": "global_broadcast", "consumable": True},
    "Map": {"effect": "reveal_full_map", "consumable": True},
    "Binoculars": {"effect": "vision_boost", "value": 1, "consumable": False},
    "Radio": {"effect": "long_range_comm", "consumable": False}
}

LIMITS = {
    "max_inventory_slots": 10
}