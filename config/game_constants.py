# -*- coding: utf-8 -*-
"""
ClawRoyale official game constants and physics constraints.
Derived from the official documentation.
"""

BASE_HP_MAX = 100.0
BASE_EP_MAX = 10.0
BASE_ATK = 25.0
BASE_DEF = 5.0

COOLDOWN_ACTION_GROUP = 30.0
HEARTBEAT_INTERVAL = 5.0

DEAD_ZONE_EXPANSION_DAY = 2
DEAD_ZONE_EXPANSION_INTERVAL = 3
DEAD_ZONE_DAMAGE_PER_SECOND = 1.34

ALERT_GAUGE_MAX = 10
ALERT_DECAY_PER_TURN = -4
ALERT_EXPLORE_PENALTY = 2
ALERT_CLEARING_PENALTY = 4

TERRAIN_MODIFIERS = {
    "plains": {"ep_cost_multiplier": 1.0, "def_bonus": 0.0, "vision_mod": 1},
    "forest": {"ep_cost_multiplier": 1.0, "def_bonus": 0.0, "vision_mod": -1},
    "hills": {"ep_cost_multiplier": 1.0, "def_bonus": 0.0, "vision_mod": 2},
    "ruins": {"ep_cost_multiplier": 1.0, "def_bonus": 0.0, "vision_mod": 0},
    "water": {"ep_cost_multiplier": 2.0, "def_bonus": 0.0, "vision_mod": 0}
}

WEATHER_EFFECTS = {
    "clear": {"atk_multiplier": 1.0, "move_ep_modifier": 0, "combat_penalty": 0.0},
    "rain": {"atk_multiplier": 0.95, "move_ep_modifier": 0, "combat_penalty": -0.05},
    "fog": {"atk_multiplier": 0.90, "move_ep_modifier": 0, "combat_penalty": -0.10},
    "storm": {"atk_multiplier": 0.85, "move_ep_modifier": 1, "combat_penalty": -0.15}
}

MONSTER_DATABASE = {
    "Wolf": {"hp": 25.0, "atk": 15.0, "def": 1.0},
    "Bear": {"hp": 30.0, "atk": 12.0, "def": 3.0},
    "Bandit": {"hp": 40.0, "atk": 25.0, "def": 5.0},
    "Guardian": {"hp": 150.0, "atk": 20.0, "def": 34.0}
}