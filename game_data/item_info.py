# game_data/item_info.py

ITEMS = {
    "emergency_food": {
        "display_name": "Emergency Food",
        "hp_bonus": 20,
        "ep_bonus": 0,
        "type": "recovery"
    },
    "bandage": {
        "display_name": "Bandage",
        "hp_bonus": 10,
        "ep_bonus": 0,
        "type": "recovery"
    },
    "medkit": {
        "display_name": "Medkit",
        "hp_bonus": 30,
        "ep_bonus": 5,
        "type": "recovery"
    },
    "energy_drink": {
        "display_name": "Energy Drink",
        "hp_bonus": 0,
        "ep_bonus": 5,
        "type": "recovery"
    },
    "megaphone": {
        "display_name": "Megaphone",
        "effect": "Global broadcast",
        "type": "utility"
    },
    "map": {
        "display_name": "Map",
        "effect": "Reveals entire map",
        "type": "utility"
    },
    "binoculars": {
        "display_name": "Binoculars",
        "effect": "Personal vision +1",
        "type": "utility"
    },
    "radio": {
        "display_name": "Radio",
        "effect": "Long-range communication",
        "type": "utility"
    }
}