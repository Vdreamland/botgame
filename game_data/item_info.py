# game_data/item_info.py

RECOVERY_ITEMS = {
    "Emergency Food": {
        "name": "Emergency Food",
        "hp_heal": 20,
        "ep_heal": 0,
        "ep_cost": 0,          # Menggunakan item memiliki biaya aksi 0 EP
        "type": "recovery"
    },
    "Bandage": {
        "name": "Bandage",
        "hp_heal": 10,
        "ep_heal": 0,
        "ep_cost": 0,
        "type": "recovery"
    },
    "Medkit": {
        "name": "Medkit",
        "hp_heal": 30,
        "ep_heal": 5,
        "ep_cost": 0,
        "type": "recovery"
    },
    "Energy Drink": {
        "name": "Energy Drink",
        "hp_heal": 0,
        "ep_heal": 5,
        "ep_cost": 0,
        "type": "recovery"
    }
}

# Berdasarkan pembaruan 1.12.0, Megaphone, Map, dan Radio telah dihapus dari game.
# Satu-satunya item utilitas yang tersisa adalah Binoculars.
UTILITY_ITEMS = {
    "Binoculars": {
        "name": "Binoculars",
        "type": "utility",
        "description": "Meningkatkan jangkauan penglihatan (vision bonus) agen saat digunakan."
    }
}

# Definisi sMoltz sebagai dropan mata uang di tanah (Free Room saja)
CURRENCY_ITEMS = {
    "sMoltz": {
        "name": "sMoltz",
        "type": "currency",
        "consumes_inventory_slot": False, # sMoltz tidak memakan slot dari batas maksimal 10 inventaris
        "description": "Koin server yang tersebar di Free Room melalui monster, peti supply, guardian, atau drop kematian agen."
    }
}