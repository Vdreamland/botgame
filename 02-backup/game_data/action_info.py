# game_data/action_info.py

ACTIONS = {
    "move": {
        "ep_cost": 1,
        "cooldown_seconds": 30,
        "is_cooldown_group": True
    },
    "explore": {
        "ep_cost": 1,
        "cooldown_seconds": 30,
        "is_cooldown_group": True
    },
    "attack": {
        "ep_cost": 1,
        "cooldown_seconds": 30,
        "is_cooldown_group": True
    },
    "use_item": {
        "ep_cost": 0,
        "cooldown_seconds": 30,
        "is_cooldown_group": True
    },
    "interact": {
        "ep_cost": 0,
        "cooldown_seconds": 30,
        "is_cooldown_group": True
    },
    "rest": {
        "ep_cost": 0,
        "cooldown_seconds": 30,
        "is_cooldown_group": True
    },
    "pickup": {
        "ep_cost": 0,
        "cooldown_seconds": 0,
        "is_cooldown_group": False
    },
    "equip": {
        "ep_cost": 0,
        "cooldown_seconds": 0,
        "is_cooldown_group": False
    },
    "talk": {
        "ep_cost": 0,
        "cooldown_seconds": 0,
        "is_cooldown_group": False
    },
    "whisper": {
        "ep_cost": 0,
        "cooldown_seconds": 0,
        "is_cooldown_group": False
    },
    "broadcast": {
        "ep_cost": 0,
        "cooldown_seconds": 0,
        "is_cooldown_group": False
    }
}

RUINS_ALERT_SYSTEM = {
    "max_ruin_gauge": 3,
    "alert_explore_increase": 2,
    "alert_clear_bonus": 4,
    "max_alert_gauge": 10,
    "alert_active_decay": -4
}