RELIC_SLOTS = {
    "R": 0,
    "G": 1,
    "B": 2
}

RELIC_AFFIXES = {
    "Ferocious": {"stat": "atk", "min": 1, "max": 10},
    "Feeble": {"stat": "atk", "min": -10, "max": -1},
    "Unyielding": {"stat": "def", "min": 1, "max": 5},
    "Fragile": {"stat": "def", "min": -5, "max": -1},
    "Insightful": {"stat": "explore", "min": 1, "max": 1},
    "Deluded": {"stat": "explore", "min": -1, "max": -1},
    "Sharp": {"stat": "item_atk", "min": 5, "max": 15},
    "Blunt": {"stat": "item_atk", "min": -15, "max": -5},
    "Sturdy": {"stat": "max_hp", "min": 1, "max": 10},
    "Sickly": {"stat": "max_hp", "min": -10, "max": -1},
    "Bountiful": {"stat": "max_ep", "min": 1, "max": 2},
    "Withered": {"stat": "max_ep", "min": -2, "max": -1},
    "Energized": {"stat": "ep_regen", "min": 1, "max": 1},
    "Sluggish": {"stat": "ep_regen", "min": -1, "max": -1},
    "Regenerating": {"stat": "hp_regen", "min": 1, "max": 3},
    "Festering": {"stat": "hp_regen", "min": -3, "max": -1}
}