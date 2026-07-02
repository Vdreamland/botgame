# game_data/world_info.py

TERRAINS = {
    "plains": {
        "display_name": "plains",
        "vision_modifier": 1,
        "move_ep_extra": 0
    },
    "forest": {
        "display_name": "forest",
        "vision_modifier": -1,
        "move_ep_extra": 0
    },
    "hills": {
        "display_name": "hills",
        "vision_modifier": 2,
        "move_ep_extra": 0
    },
    "ruins": {
        "display_name": "ruins",
        "vision_modifier": 0,
        "move_ep_extra": 0
    },
    "water": {
        "display_name": "water",
        "vision_modifier": 0,
        "move_ep_extra": 1  # 2 EP total
    }
}

WEATHER = {
    "clear": {
        "display_name": "clear",
        "vision_modifier": 0,
        "combat_modifier_percent": 0
    },
    "rain": {
        "display_name": "rain",
        "vision_modifier": -1,
        "combat_modifier_percent": -5
    },
    "fog": {
        "display_name": "fog",
        "vision_modifier": -2,
        "combat_modifier_percent": -10
    },
    "storm": {
        "display_name": "storm",
        "vision_modifier": -2,
        "combat_modifier_percent": -15
    }
}

TIME_SYSTEM = {
    "hours_per_turn": 6,
    "seconds_per_turn": 30,
    "turns_per_day": 4,
    "daytime_turns": [0, 1],
    "nighttime_turns": [2, 3],
    "max_turns": 60,
}

FACILITIES = {
    "broadcast_station": {
        "action": "broadcast",
        "effect": "Global broadcast without Megaphone"
    },
    "supply_cache": {
        "action": "loot",
        "effect": "Drops random item on the floor"
    },
    "medical_facility": {
        "action": "heal",
        "effect": "Restores agent health"
    },
    "watchtower": {
        "action": "vision_boost",
        "effect": "Temporary personal vision +2"
    },
    "cave": {
        "action": "cave_entry_exit",
        "effect": "Enters cave (vision -2, requirement +2, movement disabled)"
    }
}