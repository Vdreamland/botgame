WEAPONS = {
 "Fist": {"atk": 0, "range": 0, "ep_cost": 1},
 "Dagger": {"atk": 16, "range": 0, "ep_cost": 1},
 "Sword": {"atk": 24, "range": 0, "ep_cost": 2},
 "Katana": {"atk": 40, "range": 0, "ep_cost": 3},
 "Bow": {"atk": 8, "range": 1, "ep_cost": 1},
 "Pistol": {"atk": 15, "range": 1, "ep_cost": 2},
 "Sniper rifle": {"atk": 32, "range": 2, "ep_cost": 3}
}

ARMOR = {
 "Leather Armor": {"def": 5},
 "Chainmail": {"def": 12},
 "Plate Armor": {"def": 20}
}

RECOVERY_ITEMS = {
 "Emergency Food": {"hp_heal": 20, "ep_heal": 0},
 "Bandage": {"hp_heal": 10, "ep_heal": 0},
 "Medkit": {"hp_heal": 30, "ep_heal": 5},
 "Energy drink": {"hp_heal": 0, "ep_heal": 5}
}

UTILITY_ITEMS = {
 "Megaphone": {"effect": "broadcast", "use_type": "active"},
 "Map": {"effect": "reveal_map", "use_type": "active"},
 "Binoculars": {"effect": "vision_boost_1", "use_type": "passive"},
 "Radio": {"effect": "communication", "use_type": "passive"}
}

MONSTERS = {
 "Wolf": {"hp": 25, "atk": 15, "def": 2},
 "Bear": {"hp": 30, "atk": 12, "def": 3},
 "Bandit": {"hp": 40, "atk": 25, "def": 5}
}

GUARDIANS = {
 "Guardian": {"hp": 150, "atk": 12, "def": 120, "ep": 10, "vision": 1}
}

TERRAINS = {
 "plains": {"vision_mod": 1, "ep_cost_mod": 0},
 "forest": {"vision_mod": -1, "ep_cost_mod": 0},
 "hills": {"vision_mod": 2, "ep_cost_mod": 0},
 "ruins": {"vision_mod": 0, "ep_cost_mod": 0},
 "water": {"vision_mod": 0, "ep_cost_mod": 1}
}

WEATHERS = {
 "clear": {"vision_mod": 0, "combat_mod": 0.0},
 "rain": {"vision_mod": -1, "combat_mod": -0.05},
 "fog": {"vision_mod": -2, "combat_mod": -0.10},
 "storm": {"vision_mod": -2, "combat_mod": -0.15}
}

FACILITIES = {
 "Broadcast Station": {"effect": "broadcast"},
 "Supply Cache": {"effect": "loot"},
 "Medical Facility": {"effect": "heal"},
 "Watchtower": {"effect": "vision_boost"},
 "Cave": {"effect": "cave_in_out"}
}

GLOBAL_MAP = {
 "Silo": ["Waterfall", "Ranch", "Bunker", "Mall", "Factory"],
 "Mall": ["Silo", "Waterfall", "Hospital", "Slums", "Factory"],
 "Factory": ["Silo", "Mall", "Hospital", "Bunker", "Waterfall"],
 "Hospital": ["Mall", "Factory", "Slums", "Bunker", "Waterfall"],
 "Slums": ["Mall", "Hospital", "Bunker", "Waterfall", "Silo"],
 "Bunker": ["Silo", "Factory", "Hospital", "Slums", "Waterfall"],
 "Waterfall": ["Silo", "Mall", "Factory", "Hospital", "Slums", "Bunker"],
 "Ranch": ["Silo", "Prison", "Bunker", "Relic", "School"],
 "Prison": ["Ranch", "Bunker", "School", "Library", "Uptown"],
 "School": ["Ranch", "Prison", "Barracks", "Stadium", "Market", "Meadow", "Library"],
 "Barracks": ["School", "Stadium", "Market", "Meadow", "Police Station", "Hangar"],
 "Stadium": ["School", "Barracks", "Market", "Meadow", "Police Station", "Hangar"],
 "Market": ["School", "Barracks", "Stadium", "Meadow", "Police Station", "Hangar", "Orchard"],
 "Meadow": ["School", "Barracks", "Stadium", "Market", "Police Station", "Hangar"],
 "Police Station": ["Hangar", "Arsenal", "Castle", "Oil Rig", "Barracks", "Tower"],
 "Hangar": ["Police Station", "Arsenal", "Castle", "Oil Rig", "Barracks", "Tower", "Stadium"],
 "Arsenal": ["Police Station", "Hangar", "Castle", "Oil Rig", "Tower", "Shrine"],
 "Castle": ["Police Station", "Hangar", "Arsenal", "Oil Rig", "Tower"],
 "Oil Rig": ["Police Station", "Hangar", "Arsenal", "Castle", "Tower"],
 "Tower": ["Police Station", "Hangar", "Arsenal", "Castle", "Oil Rig", "Canyon", "Barn", "Pier", "Relic"],
 "Canyon": ["Tower", "Barn", "Pier", "Relic", "Observatory"],
 "Barn": ["Tower", "Canyon", "Pier", "Relic", "Observatory"],
 "Pier": ["Tower", "Canyon", "Barn", "Relic", "Observatory", "Orchard"],
 "Relic": ["Tower", "Canyon", "Barn", "Pier", "Observatory", "Ranch"],
 "Orchard": ["Pier", "Market", "Theater", "Outpost", "Bank"],
 "Theater": ["Orchard", "Pier", "Outpost", "Bank", "Windmill"],
 "Outpost": ["Orchard", "Theater", "Bank", "Windmill"],
 "Bank": ["Orchard", "Theater", "Outpost", "Windmill"],
 "Windmill": ["Suburbs", "Pond", "Valley", "Beach", "Theater", "Outpost", "Bank"],
 "Suburbs": ["Windmill", "Pond", "Valley", "Beach", "Garage"],
 "Pond": ["Windmill", "Suburbs", "Valley", "Beach", "Gas Station"],
 "Valley": ["Windmill", "Suburbs", "Pond", "Beach", "Outpost"],
 "Beach": ["Windmill", "Suburbs", "Pond", "Valley", "Sanctuary"],
 "Sanctuary": ["Beach", "Outpost", "Ranch", "Uptown"],
 "Uptown": ["Sanctuary", "Prison", "Downtown", "Station", "Reactor"],
 "Downtown": ["Uptown", "Station", "Reactor", "Shrine", "Library"],
 "Station": ["Uptown", "Downtown", "Reactor", "Shrine", "Library"],
 "Reactor": ["Uptown", "Downtown", "Station", "Shrine", "Library"],
 "Shrine": ["Arsenal", "Uptown", "Downtown", "Station", "Reactor", "Library"],
 "Library": ["Prison", "School", "Downtown", "Station", "Reactor", "Shrine"]
}