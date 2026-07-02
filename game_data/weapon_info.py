# game_data/weapon_info.py

WEAPONS = {
    "Fist": {
        "name": "Fist",
        "atk_bonus": 0,
        "range": 0,            # Jarak serang 0 (harus berada di satu region yang sama dengan target)
        "ep_cost": 1,          # Membutuhkan 1 EP untuk melakukan aksi 'attack'
        "type": "melee"
    },
    "Dagger": {
        "name": "Dagger",
        "atk_bonus": 16,
        "range": 0,
        "ep_cost": 1,
        "type": "melee"
    },
    "Sword": {
        "name": "Sword",
        "atk_bonus": 24,
        "range": 0,
        "ep_cost": 2,          # Membutuhkan minimal 2 EP untuk menyerang
        "type": "melee"
    },
    "Katana": {
        "name": "Katana",
        "atk_bonus": 40,
        "range": 0,
        "ep_cost": 3,          # Membutuhkan minimal 3 EP untuk menyerang (High melee damage)
        "type": "melee"
    },
    "Bow": {
        "name": "Bow",
        "atk_bonus": 8,
        "range": 1,            # Jarak serang melompati 1 region di sebelahnya
        "ep_cost": 1,
        "type": "ranged"
    },
    "Pistol": {
        "name": "Pistol",
        "atk_bonus": 15,
        "range": 1,
        "ep_cost": 2,
        "type": "ranged"
    },
    "Sniper rifle": {
        "name": "Sniper rifle",
        "atk_bonus": 32,
        "range": 2,            # Jarak serang melompati hingga 2 region (High ranged damage)
        "ep_cost": 3,
        "type": "ranged"
    }
}