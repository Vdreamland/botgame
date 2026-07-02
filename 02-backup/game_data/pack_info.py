# game_data/pack_info.py

PACKS = {
    "moltz_expert": {
        "category_id": 0,
        "display_name": "Moltz Expert",
        "is_main_only": False,
        "sub_multiplier": 0.5,
        "t1": {"high": 12, "middle": 8, "low": 4},
        "t2": {"high": 9, "middle": 6, "low": 3},
        "t3": {"high": 6, "middle": 4, "low": 2}
    },
    "item_expert": {
        "category_id": 1,
        "display_name": "Item Expert",
        "is_main_only": False,
        "sub_multiplier": 0.5,
        "t1": {"relic_item_atk_divisor": 20.0, "multiplier": 2.0, "min_bonus": 0.7},
        "t2": {"relic_item_atk_divisor": 20.0, "multiplier": 1.5, "min_bonus": 0.6},
        "t3": {"relic_item_atk_divisor": 20.0, "multiplier": 1.0, "min_bonus": 0.5}
    },
    "goliath": {
        "category_id": 2,
        "display_name": "Goliath",
        "is_main_only": False,
        "sub_multiplier": 0.5,
        "t1": {"atk_multiplier": 0.85, "extra_ep": 1, "is_aoe": True},
        "t2": {"atk_multiplier": 0.75, "extra_ep": 1, "is_aoe": True},
        "t3": {"atk_multiplier": 0.65, "extra_ep": 1, "is_aoe": True}
    },
    "thorns": {
        "category_id": 3,
        "display_name": "Thorns",
        "is_main_only": False,
        "sub_multiplier": 0.5,
        "t1": {"dmg_reduction_ratio": 0.50, "reflect_ratio": 1.00, "dealt_dmg_multiplier": 0.20},
        "t2": {"dmg_reduction_ratio": 0.45, "reflect_ratio": 0.95, "dealt_dmg_multiplier": 0.20},
        "t3": {"dmg_reduction_ratio": 0.40, "reflect_ratio": 0.90, "dealt_dmg_multiplier": 0.20}
    },
    "scout": {
        "category_id": 4,
        "display_name": "Scout",
        "is_main_only": True,
        "sub_multiplier": 0.0,
        "t1": {"vision_bonus": 2, "move_ep_discount": 2, "dealt_dmg_multiplier": 0.80},
        "t2": {"vision_bonus": 2, "move_ep_discount": 1, "dealt_dmg_multiplier": 0.70},
        "t3": {"vision_bonus": 1, "move_ep_discount": 0, "dealt_dmg_multiplier": 0.60}
    },
    "ruin_expert": {
        "category_id": 5,
        "display_name": "Ruin Expert",
        "is_main_only": False,
        "sub_multiplier": 1.0,
        "t1": {"instant_grant": True, "alert_max_on_clear": True, "guardian_dmg_multiplier": 1.50},
        "t2": {"instant_grant": True, "alert_max_on_clear": True, "guardian_dmg_multiplier": 2.00},
        "t3": {"instant_grant": True, "alert_max_on_clear": True, "guardian_dmg_multiplier": 2.50}
    },
    "berserker": {
        "category_id": 6,
        "display_name": "Berserker",
        "is_main_only": False,
        "sub_multiplier": None,
        "t1": {"hp_threshold": 50, "main_dmg_multiplier": 1.7, "sub_dmg_multiplier": 1.3},
        "t2": {"hp_threshold": 50, "main_dmg_multiplier": 1.5, "sub_dmg_multiplier": 1.2},
        "t3": {"hp_threshold": 50, "main_dmg_multiplier": 1.3, "sub_dmg_multiplier": 1.1}
    },
    "double_attack": {
        "category_id": 7,
        "display_name": "Double Attack",
        "is_main_only": False,
        "sub_multiplier": None,
        "t1": {"hit_count": 2, "main_hit_dmg_multiplier": 0.65, "sub_hit_dmg_multiplier": 0.55, "extra_ep": 1},
        "t2": {"hit_count": 2, "main_hit_dmg_multiplier": 0.55, "sub_hit_dmg_multiplier": 0.525, "extra_ep": 1},
        "t3": {"hit_count": 2, "main_hit_dmg_multiplier": 0.50, "sub_hit_dmg_multiplier": 0.50, "extra_ep": 1}
    },
    "heart_of_the_giant": {
        "category_id": 8,
        "display_name": "Heart of the Giant",
        "is_main_only": False,
        "sub_multiplier": 0.5,
        "t1": {"heal_item_bonus": 0.75, "self_heal_pct": 0.03, "base_def_override": 0, "base_atk_offset": -5},
        "t2": {"heal_item_bonus": 0.50, "self_heal_pct": 0.02, "base_def_override": 0, "base_atk_offset": -5},
        "t3": {"heal_item_bonus": 0.25, "self_heal_pct": 0.01, "base_def_override": 0, "base_atk_offset": -5}
    },
    "bomber": {
        "category_id": 9,
        "display_name": "Bomber",
        "is_main_only": False,
        "sub_multiplier": 0.5,
        "t1": {"max_bombs_per_turn": 3, "bomb_dmg_atk_ratio": 0.20},
        "t2": {"max_bombs_per_turn": 2, "bomb_dmg_atk_ratio": 0.15},
        "t3": {"max_bombs_per_turn": 1, "bomb_dmg_atk_ratio": 0.10}
    },
    "trail_ward": {
        "category_id": 10,
        "display_name": "Trail Ward",
        "is_main_only": False,
        "sub_multiplier": None,
        "t1": {"main_initial_wards": 3, "sub_initial_wards": 2, "ward_vision_bonus": 1},
        "t2": {"main_initial_wards": 2, "sub_initial_wards": 1, "ward_vision_bonus": 1},
        "t3": {"main_initial_wards": 1, "sub_initial_wards": 0, "ward_vision_bonus": 1}
    },
    "ranged": {
        "category_id": 11,
        "display_name": "Ranged",
        "is_main_only": False,
        "sub_multiplier": None,
        "t1": {"range_bonus": 1, "dmg_bonus_pct": 15, "no_melee": True, "no_same_region": True},
        "t2": {"range_bonus": 1, "dmg_bonus_pct": 10, "no_melee": True, "no_same_region": True},
        "t3": {"range_bonus": 1, "dmg_bonus_pct": 5, "no_melee": True, "no_same_region": True}
    },
    "sword_master": {
        "category_id": 12,
        "display_name": "Sword Master",
        "is_main_only": False,
        "sub_multiplier": None,
        "t1": {"no_ranged": True, "main_ignore_ranged_hops_min": 1, "sub_ignore_ranged_hops_min": 2, "main_relic_item_atk_multiplier": 1.0, "sub_relic_item_atk_multiplier": 0.5},
        "t2": {"no_ranged": True, "main_ignore_ranged_hops_min": 1, "sub_ignore_ranged_hops_min": 2, "main_relic_item_atk_multiplier": 0.75, "sub_relic_item_atk_multiplier": 0.5},
        "t3": {"no_ranged": True, "main_ignore_ranged_hops_min": 1, "sub_ignore_ranged_hops_min": 2, "main_relic_item_atk_multiplier": 0.50, "sub_relic_item_atk_multiplier": 0.5}
    },
    "duelist": {
        "category_id": 13,
        "display_name": "Duelist",
        "is_main_only": False,
        "sub_multiplier": 0.5,
        "t1": {"isolated_relic_atk_multiplier": 0.9, "isolated_relic_def_multiplier": 0.9},
        "t2": {"isolated_relic_atk_multiplier": 0.7, "isolated_relic_def_multiplier": 0.7},
        "t3": {"isolated_relic_atk_multiplier": 0.5, "isolated_relic_def_multiplier": 0.5}
    },
    "raider": {
        "category_id": 14,
        "display_name": "Raider",
        "is_main_only": False,
        "sub_multiplier": None,
        "t1": {"steal_inventory_slot": 1, "no_floor_pickup": True}
    },
    "last_stand": {
        "category_id": 15,
        "display_name": "Last Stand",
        "is_main_only": False,
        "sub_multiplier": None,
        "t1": {"survive_lethal_hp": 1, "main_berserk_turns": 3, "sub_berserk_turns": 1, "hp_regen_pct_bonus": 5.0, "atk_multiplier_of_regen": 10.0},
        "t2": {"survive_lethal_hp": 1, "main_berserk_turns": 2, "sub_berserk_turns": 1, "hp_regen_pct_bonus": 4.0, "atk_multiplier_of_regen": 10.0},
        "t3": {"survive_lethal_hp": 1, "main_berserk_turns": 1, "sub_berserk_turns": 1, "hp_regen_pct_bonus": 3.0, "atk_multiplier_of_regen": 10.0}
    },
    "iron_heart": {
        "category_id": 16,
        "display_name": "Iron Heart",
        "is_main_only": False,
        "sub_multiplier": 0.5,
        "t1": {"extra_hp_div": 10, "flat_hp_gain": 5, "def_gain": 1, "max_def_stack": 10, "dealt_dmg_multiplier": 0.90},
        "t2": {"extra_hp_div": 10, "flat_hp_gain": 3, "def_gain": 1, "max_def_stack": 10, "dealt_dmg_multiplier": 0.80},
        "t3": {"extra_hp_div": 10, "flat_hp_gain": 1, "def_gain": 1, "max_def_stack": 10, "dealt_dmg_multiplier": 0.70}
    },
    "sunflame_cloak": {
        "category_id": 17,
        "display_name": "Sunflame Cloak",
        "is_main_only": False,
        "sub_multiplier": 0.5,
        "t1": {"aura_radius": 1, "damage_coef": 1.0, "dealt_dmg_multiplier": 0.65},
        "t2": {"aura_radius": 1, "damage_coef": 0.8, "dealt_dmg_multiplier": 0.55},
        "t3": {"aura_radius": 0, "damage_coef": 0.6, "dealt_dmg_multiplier": 0.45}
    },
    "assassin": {
        "category_id": 18,
        "display_name": "Assassin",
        "is_main_only": True,
        "sub_multiplier": 0.0,
        "t1": {"stealth_expose_vision_bonus": 3, "bonus_dmg_multiplier_of_total": 0.6, "exposed_turns": 2},
        "t2": {"stealth_expose_vision_bonus": 2, "bonus_dmg_multiplier_of_total": 0.5, "exposed_turns": 2},
        "t3": {"stealth_expose_vision_bonus": 1, "bonus_dmg_multiplier_of_total": 0.4, "exposed_turns": 2}
    },
    "pickpocket": {
        "category_id": 19,
        "display_name": "Pickpocket",
        "is_main_only": False,
        "sub_multiplier": None,
        "t1": {"max_steal_smoltz": 3}
    }
}