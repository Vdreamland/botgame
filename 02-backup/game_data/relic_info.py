# game_data/relic_info.py

RELICS_RULES = {
    "slots": {
        0: "Red",
        1: "Green",
        2: "Blue"
    },
    "affixes": {
        "atk": {
            "display_positive": "Ferocious",
            "display_negative": "Feeble",
            "min_val": 1,
            "max_val": 10
        },
        "def": {
            "display_positive": "Unyielding",
            "display_negative": "Fragile",
            "min_val": 1,
            "max_val": 5
        },
        "explore": {
            "display_positive": "Insightful",
            "display_negative": "Deluded",
            "min_val": 1,
            "max_val": 1
        },
        "item_atk": {
            "display_positive": "Sharp",
            "display_negative": "Blunt",
            "min_val": 5,
            "max_val": 15
        },
        "max_hp": {
            "display_positive": "Sturdy",
            "display_negative": "Sickly",
            "min_val": 1,
            "max_val": 10
        },
        "max_ep": {
            "display_positive": "Bountiful",
            "display_negative": "Withered",
            "min_val": 1,
            "max_val": 2
        },
        "ep_regen": {
            "display_positive": "Energized",
            "display_negative": "Sluggish",
            "min_val": 1,
            "max_val": 1
        },
        "hp_regen": {
            "display_positive": "Regenerating",
            "display_negative": "Festering",
            "min_val": 1,
            "max_val": 3
        }
    }
}