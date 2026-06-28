# -*- coding: utf-8 -*-
"""
ClawRoyale complete item database.
Provides functional mapping for weapons, armors, consumables, and relics.
"""

from typing import Dict, Any

ITEM_DATABASE: Dict[str, Dict[str, Any]] = {
    # --- SENJATA (WEAPONS) ---
    "weap_rust_blade": {
        "name": "Rusty Iron Blade",
        "category": "weapon",
        "sub_category": "melee",
        "range": 0,                    # Jarak 0 berarti hanya kontak jarak dekat (melee) [11]
        "atk_bonus": 5.0,
        "ep_usage": 3.0
    },
    "weap_steel_sword": {
        "name": "Forged Steel Sword",
        "category": "weapon",
        "sub_category": "melee",
        "range": 0,
        "atk_bonus": 12.0,
        "ep_usage": 4.0
    },
    "weap_pulse_rifle": {
        "name": "Assault Pulse Rifle",
        "category": "weapon",
        "sub_category": "ranged",
        "range": 2,                    # Jarak serang optimal 1-2 kotak [11]
        "atk_bonus": 8.0,
        "ep_usage": 5.0
    },
    "weap_hunting_bow": {
        "name": "Silent Hunting Bow",
        "category": "weapon",
        "sub_category": "ranged",
        "range": 2,
        "atk_bonus": 6.0,
        "ep_usage": 3.0
    },

    # --- PELINDUNG (ARMOR) ---
    "armor_leather_jacket": {
        "name": "Scavenger Leather Vest",
        "category": "armor",
        "def_bonus": 3.0
    },
    "armor_riot_plate": {
        "name": "Heavy Duty Riot Plate",
        "category": "armor",
        "def_bonus": 8.0
    },

    # --- OBAT / KONSUMSI (CONSUMABLES) ---
    "item_bandage": {
        "name": "Field Bandage",
        "category": "consumable",
        "heal_value": 20.0,
        "ep_recovery": 0.0
    },
    "item_medkit": {
        "name": "Standard Combat Medkit",
        "category": "consumable",
        "heal_value": 55.0,
        "ep_recovery": 0.0
    },
    "item_energy_drink": {
        "name": "smoltz Energy Soda",
        "category": "consumable",
        "heal_value": 5.0,
        "ep_recovery": 15.0
    },

    # --- RELIC (RGB SLOTS) ---
    "relic_ruby_shard": {
        "name": "Crimson Ruby Shard",
        "category": "relic",
        "slot_color": "red",
        "bonus_type": "atk_multiplier",
        "bonus_value": 0.05            # +5% ATK
    },
    "relic_emerald_ring": {
        "name": "Jade Emerald Ring",
        "category": "relic",
        "slot_color": "green",
        "bonus_type": "def_multiplier",
        "bonus_value": 0.05            # +5% DEF
    },
    "relic_sapphire_gem": {
        "name": "Deep Sapphire Gem",
        "category": "relic",
        "slot_color": "blue",
        "bonus_type": "ep_multiplier",
        "bonus_value": 0.05            # +5% EP
    }
}