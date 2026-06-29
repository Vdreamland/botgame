TERRAIN = {
    "plains": {"vision_modifier": 1, "extra_ep": 0},
    "forest": {"vision_modifier": -1, "extra_ep": 0},
    "hills": {"vision_modifier": 2, "extra_ep": 0},
    "ruins": {"vision_modifier": 0, "extra_ep": 0},
    "water": {"vision_modifier": 0, "extra_ep": 1}
}

WEATHER = {
    "clear": {"vision_modifier": 0, "extra_ep": 0, "combat_modifier": 0.0},
    "rain": {"vision_modifier": -1, "extra_ep": 0, "combat_modifier": -0.05},
    "fog": {"vision_modifier": -2, "extra_ep": 0, "combat_modifier": -0.10},
    "storm": {"vision_modifier": -2, "extra_ep": 1, "combat_modifier": -0.15}
}