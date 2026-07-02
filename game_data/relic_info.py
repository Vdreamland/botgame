# game_data/relic_info.py

# Pembagian slot relic berdasarkan warna primer relic yang didapatkan
RELIC_SLOTS = {
    "Red": 0,                  # Relic merah hanya dapat dimasukkan ke Slot 0
    "Green": 1,                # Relic hijau hanya dapat dimasukkan ke Slot 1
    "Blue": 2                  # Relic biru hanya dapat dimasukkan ke Slot 2
}

# Batasan nilai efek afiks (Prefix) relic positif dan negatif
RELIC_AFFIXES = {
    "atk": {
        "positive": {"prefix": "Ferocious", "min_val": 1, "max_val": 10},
        "negative": {"prefix": "Feeble", "min_val": -10, "max_val": -1}
    },
    "def": {
        "positive": {"prefix": "Unyielding", "min_val": 1, "max_val": 5},
        "negative": {"prefix": "Fragile", "min_val": -5, "max_val": -1}
    },
    "explore": {
        "positive": {"prefix": "Insightful", "val": 1},
        "negative": {"prefix": "Deluded", "val": -1}
    },
    "item_atk": {
        "positive": {"prefix": "Sharp", "min_val": 5, "max_val": 15},
        "negative": {"prefix": "Blunt", "min_val": -15, "max_val": -5}
    },
    "max_hp": {
        "positive": {"prefix": "Sturdy", "min_val": 1, "max_val": 10},
        "negative": {"prefix": "Sickly", "min_val": -10, "max_val": -1}
    },
    "max_ep": {
        "positive": {"prefix": "Bountiful", "min_val": 1, "max_val": 2},
        "negative": {"prefix": "Withered", "min_val": -2, "max_val": -1}
    },
    "ep_regen": {
        "positive": {"prefix": "Energized", "val": 1},
        "negative": {"prefix": "Sluggish", "val": -1}
    },
    "hp_regen": {
        "positive": {"prefix": "Regenerating", "min_val": 1, "max_val": 3},
        "negative": {"prefix": "Festering", "min_val": -3, "max_val": -1}
    }
}