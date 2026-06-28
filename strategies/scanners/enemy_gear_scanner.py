# -*- coding: utf-8 -*-
"""
ClawRoyale Enemy Gear Scanner.
Analyzes enemy weapons, armor, and fullSet state to estimate effective damage potential [9, 11].
"""

from typing import Dict, Any
from config.item_registry import ITEM_DATABASE
from config.game_constants import BASE_ATK, BASE_DEF


class EnemyGearScanner:
    @staticmethod
    def calculate_effective_combat_stats(enemy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates effective Attack (ATK) and Defense (DEF) stats for the enemy.
        Respects the 'fullSet' rule: if fullSet is False, relic/pack bonuses are ignored [9].
        """
        loadout = enemy_data.get("loadout", {})
        weapon_id = loadout.get("weapon", "")
        armor_id = loadout.get("armor", "")
        has_full_set = bool(loadout.get("fullSet", False))

        # 1. Hitung Nilai Serangan Dasar + Senjata [11]
        weapon_bonus = 0.0
        weapon_range = 0
        weapon_type = "melee"

        if weapon_id:
            # Normalisasi pencarian tipe senjata secara case-insensitive dan spasi
            normalized_weapon = weapon_id.lower().replace("_", " ").strip()
            matched_weapon = None
            for db_key, db_info in ITEM_DATABASE.items():
                if db_key.lower().replace("_", " ").strip() == normalized_weapon:
                    matched_weapon = db_info
                    break

            if matched_weapon:
                weapon_bonus = float(matched_weapon.get("atk_bonus", 0.0))
                weapon_range = int(matched_weapon.get("range", 0))
                weapon_type = matched_weapon.get("sub_category", "melee")

        effective_atk = BASE_ATK + weapon_bonus

        # 2. Hitung Nilai Pertahanan Dasar + Armor
        armor_bonus = 0.0
        if armor_id:
            # Normalisasi pencarian tipe armor secara case-insensitive
            normalized_armor = armor_id.lower().replace("_", " ").strip()
            matched_armor = None
            for db_key, db_info in ITEM_DATABASE.items():
                if db_key.lower().replace("_", " ").strip() == normalized_armor:
                    matched_armor = db_info
                    break

            if matched_armor:
                armor_bonus = float(matched_armor.get("def_bonus", 0.0))

        effective_def = BASE_DEF + armor_bonus

        # 3. Hitung Bonus Relic (Hanya Aktif Jika fullSet Terpenuhi) [9]
        relics = loadout.get("relics", [])
        relic_atk_multiplier = 1.0
        relic_def_multiplier = 1.0

        if has_full_set and relics:
            for r_id in relics:
                normalized_relic = r_id.lower().replace("_", " ").strip()
                matched_relic = None
                for db_key, db_info in ITEM_DATABASE.items():
                    if db_key.lower().replace("_", " ").strip() == normalized_relic:
                        matched_relic = db_info
                        break

                if matched_relic:
                    bonus_type = matched_relic.get("bonus_type", "")
                    bonus_val = float(matched_relic.get("bonus_value", 0.0))

                    if bonus_type == "atk_multiplier":
                        relic_atk_multiplier += bonus_val
                    elif bonus_type == "def_multiplier":
                        relic_def_multiplier += bonus_val

        # Terapkan pengali relic [9]
        effective_atk *= relic_atk_multiplier
        effective_def *= relic_def_multiplier

        return {
            "effective_atk": effective_atk,
            "effective_def": effective_def,
            "weapon_range": weapon_range,
            "weapon_type": weapon_type,
            "has_full_set": has_full_set
        }