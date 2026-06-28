# -*- coding: utf-8 -*-
"""
ClawRoyale complete item database.
Provides functional mapping for weapons, armors, consumables, and relics.
"""

ITEM_DATABASE = {
    "Fist": {
        "name": "Fist (default)",
        "category": "weapon",
        "sub_category": "melee",
        "range": 0,
        "atk_bonus": 0.0,
        "ep_usage": 0.0
    },
    "Dagger": {
        "name": "Dagger",
        "category": "weapon",
        "sub_category": "melee",
        "range": 0,
        "atk_bonus": 16.0,
        "ep_usage": 0.0
    },
    "Sword": {
        "name": "Sword",
        "category": "weapon",
        "sub_category": "melee",
        "range": 0,
        "atk_bonus": 24.0,
        "ep_usage": 0.0
    },
    "Katana": {
        "name": "Katana",
        "category": "weapon",
        "sub_category": "melee",
        "range": 0,
        "atk_bonus": 40.0,
        "ep_usage": 2.0
    },
    "Bow": {
        "name": "Bow",
        "category": "weapon",
        "sub_category": "ranged",
        "range": 1,
        "atk_bonus": 8.0,
        "ep_usage": 0.0
    },
    "Pistol": {
        "name": "Pistol",
        "category": "weapon",
        "sub_category": "ranged",
        "range": 1,
        "atk_bonus": 15.0,
        "ep_usage": 0.0
    },
    "Sniper rifle": {
        "name": "Sniper rifle",
        "category": "weapon",
        "sub_category": "ranged",
        "range": 2,
        "atk_bonus": 32.0,
        "ep_usage": 2.0
    },
    "Emergency Food": {
        "name": "Emergency Food",
        "category": "consumable",
        "heal_value": 20.0,
        "ep_recovery": 0.0
    },
    "Bandage": {
        "name": "Bandage",
        "category": "consumable",
        "heal_value": 10.0,
        "ep_recovery": 0.0
    },
    "Medkit": {
        "name": "Medkit",
        "category": "consumable",
        "heal_value": 30.0,
        "ep_recovery": 5.0
    },
    "Energy Drink": {
        "name": "Energy Drink",
        "category": "consumable",
        "heal_value": 0.0,
        "ep_recovery": 5.0
    },
    "Megaphone": {
        "name": "Megaphone",
        "category": "utility"
    },
    "Map": {
        "name": "Map",
        "category": "utility"
    },
    "Binoculars": {
        "name": "Binoculars",
        "category": "utility"
    },
    "Radio": {
        "name": "Radio",
        "category": "utility"
    },
    "Red Relic": {
        "name": "Red Relic",
        "category": "relic",
        "slot_color": "red"
    },
    "Green Relic": {
        "name": "Green Relic",
        "category": "relic",
        "slot_color": "green"
    },
    "Blue Relic": {
        "name": "Blue Relic",
        "category": "relic",
        "slot_color": "blue"
    }
}