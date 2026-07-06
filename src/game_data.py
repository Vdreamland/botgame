# WEAPONS
WEAPONS = {
    "Fist": {"atk": 0, "range": 0, "ep_cost": 1},
    "Dagger": {"atk": 16, "range": 0, "ep_cost": 1},
    "Sword": {"atk": 24, "range": 0, "ep_cost": 2},
    "Katana": {"atk": 40, "range": 0, "ep_cost": 3},
    "Bow": {"atk": 8, "range": 1, "ep_cost": 1},
    "Pistol": {"atk": 15, "range": 1, "ep_cost": 2},
    "Sniper rifle": {"atk": 32, "range": 2, "ep_cost": 3}
}

# ARMOR
ARMOR = {
    "Leather Armor": {"def": 5},
    "Chainmail": {"def": 12},
    "Plate Armor": {"def": 20}
}

# RECOVERY ITEMS
RECOVERY_ITEMS = {
    "Emergency Food": {"hp_heal": 20, "ep_heal": 0},
    "Bandage": {"hp_heal": 10, "ep_heal": 0},
    "Medkit": {"hp_heal": 30, "ep_heal": 5},
    "Energy Drink": {"hp_heal": 0, "ep_heal": 5}
}

# UTILITY ITEMS
UTILITY_ITEMS = {
    "Megaphone": {"effect": "broadcast"},
    "Map": {"effect": "reveal_map"},
    "Binoculars": {"effect": "vision_boost_1"},
    "Radio": {"effect": "communication"}
}

# MONSTERS
MONSTERS = {
    "Wolf": {"hp": 25, "atk": 15, "def": 1},
    "Bear": {"hp": 30, "atk": 12, "def": 3},
    "Bandit": {"hp": 40, "atk": 25, "def": 5}
}

# GUARDIANS
GUARDIANS = {
    "Guardian": {"hp": 150, "atk": 20, "def": 34, "ep": 10, "vision": 1}
}

# TERRAINS
TERRAINS = {
    "plains": {"vision_mod": 1, "ep_cost_mod": 0},
    "forest": {"vision_mod": -1, "ep_cost_mod": 0},
    "hills": {"vision_mod": 2, "ep_cost_mod": 0},
    "ruins": {"vision_mod": 0, "ep_cost_mod": 0},
    "water": {"vision_mod": 0, "ep_cost_mod": 1}
}

# WEATHERS
WEATHERS = {
    "clear": {"vision_mod": 0, "combat_mod": 0.0},
    "rain": {"vision_mod": -1, "combat_mod": -0.05},
    "fog": {"vision_mod": -2, "combat_mod": -0.10},
    "storm": {"vision_mod": -2, "combat_mod": -0.15}
}

# FACILITIES
FACILITIES = {
    "Broadcast Station": {"effect": "broadcast"},
    "Supply Cache": {"effect": "loot"},
    "Medical Facility": {"effect": "heal"},
    "Watchtower": {"effect": "vision_boost"},
    "Cave": {"effect": "cave_in_out"}
}