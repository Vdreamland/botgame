# game_data/pack_info.py

# 20 kategori pack yang digunakan sebagai Main Pack atau Sub Pack di sistem Loadout
PACK_CATEGORIES = {
    "CAT-00": {
        "name": "Moltz Expert",
        "description": "Konversi senjata/armor yang ditemukan di dalam arena menjadi koin Moltz.",
        "tiers": {
            "T1": {"high": 12, "middle": 8, "low": 4},
            "T2": {"high": 9, "middle": 6, "low": 3},
            "T3": {"high": 6, "middle": 4, "low": 2}
        },
        "sub_attenuation": 0.5, # Jika dipasang di slot Sub, nilai konversi dikalikan 0.5 (dipotong setengah)
        "main_only": False
    },
    "CAT-01": {
        "name": "Item Expert",
        "description": "Menambahkan damage item ATK dari Relic saat menggunakan senjata.",
        "tiers": {
            "T1": "Max(Relic ItemATK / 20 * 2, 0.7)",
            "T2": "Max(Relic ItemATK / 20 * 1.5, 0.6)",
            "T3": "Max(Relic ItemATK / 20 * 1, 0.5)"
        },
        "sub_attenuation": 0.5,
        "main_only": False
    },
    "CAT-02": {
        "name": "Goliath",
        "description": "Serangan area (AoE) ke wilayah target. Meningkatkan biaya serangan sebesar +1 EP.",
        "tiers": {
            "T1": {"weapon_atk_multiplier": 0.85},
            "T2": {"weapon_atk_multiplier": 0.75},
            "T3": {"weapon_atk_multiplier": 0.65}
        },
        "sub_attenuation": "multiplier_halved",
        "main_only": False
    },
    "CAT-03": {
        "name": "Thorns",
        "description": "Mengurangi damage yang diterima dan memantulkan persentase damage tersebut kembali ke penyerang. Damage yang dikeluarkan mandiri dikalikan x0.2.",
        "tiers": {
            "T1": {"damage_reduction": 0.50, "reflect_percent": 1.00},
            "T2": {"damage_reduction": 0.45, "reflect_percent": 0.95},
            "T3": {"damage_reduction": 0.40, "reflect_percent": 0.90}
        },
        "sub_attenuation": "halved_no_def_bonus",
        "main_only": False
    },
    "CAT-04": {
        "name": "Scout",
        "description": "Hanya dapat digunakan di slot Main. Memberikan tambahan penglihatan dan mengurangi biaya EP untuk bergerak.",
        "tiers": {
            "T1": {"vision_bonus": 2, "move_ep_bonus": -2, "dealt_damage_multiplier": 0.8},
            "T2": {"vision_bonus": 2, "move_ep_bonus": -1, "dealt_damage_multiplier": 0.7},
            "T3": {"vision_bonus": 1, "move_ep_bonus": 0, "dealt_damage_multiplier": 0.6}
        },
        "sub_attenuation": None,
        "main_only": True      # Tidak diperkenankan ditaruh di slot Sub Pack
    },
    "CAT-05": {
        "name": "Ruin Expert",
        "description": "Mendapatkan relic/pack secara langsung saat ditemukan tanpa perlu bertahan hidup sampai akhir game. Namun, alert gauge langsung maksimal dan Guardian memberikan damage berkali lipat.",
        "tiers": {
            "T1": {"guardian_dmg_multiplier": 1.5},
            "T2": {"guardian_dmg_multiplier": 2.0},
            "T3": {"guardian_dmg_multiplier": 2.5}
        },
        "sub_attenuation": 1.0,  # Efek sub pack sama persis dengan main pack
        "main_only": False
    },
    "CAT-06": {
        "name": "Berserker",
        "description": "Meningkatkan damage yang dihasilkan ketika HP di bawah 50.",
        "tiers": {
            "T1": {"main_multiplier": 1.7, "sub_multiplier": 1.3},
            "T2": {"main_multiplier": 1.5, "sub_multiplier": 1.2},
            "T3": {"main_multiplier": 1.3, "sub_multiplier": 1.1}
        },
        "sub_attenuation": "specific",
        "main_only": False
    },
    "CAT-07": {
        "name": "Double Attack",
        "description": "Menyerang dua kali berturut-turut dalam satu aksi attack dengan tambahan biaya +1 EP.",
        "tiers": {
            "T1": {"main_dmg_factor": 0.65, "sub_dmg_factor": 0.55},
            "T2": {"main_dmg_factor": 0.55, "sub_dmg_factor": 0.525},
            "T3": {"main_dmg_factor": 0.50, "sub_dmg_factor": 0.50}
        },
        "sub_attenuation": "specific",
        "main_only": False
    },
    "CAT-08": {
        "name": "Heart of the Giant",
        "description": "Meningkatkan pemulihan heal, memberikan pasif self-heal per giliran, namun mengurangi ATK bawaan dan menghapus pertahanan dasar (menjadi 0 DEF).",
        "tiers": {
            "T1": {"heal_boost": 0.75, "regen_turn": 0.03, "base_def": 0, "flat_dmg_taken": 5, "base_atk_bonus": -5},
            "T2": {"heal_boost": 0.50, "regen_turn": 0.02, "base_def": 0, "flat_dmg_taken": 5, "base_atk_bonus": -5},
            "T3": {"heal_boost": 0.25, "regen_turn": 0.01, "base_def": 0, "flat_dmg_taken": 5, "base_atk_bonus": -5}
        },
        "sub_attenuation": "heal_effects_halved",
        "main_only": False
    },
    "CAT-09": {
        "name": "Bomber",
        "description": "Mengubah item yang dilewati di jalanan menjadi perangkap bom.",
        "tiers": {
            "T1": {"max_bombs": 3, "atk_multiplier": 0.20},
            "T2": {"max_bombs": 2, "atk_multiplier": 0.15},
            "T3": {"max_bombs": 1, "atk_multiplier": 0.10}
        },
        "sub_attenuation": 0.5,  # Damage bom dipotong setengah
        "main_only": False
    },
    "CAT-10": {
        "name": "Trail Ward",
        "description": "Mulai permainan dengan ward pelacak yang meningkatkan area penglihatan (+1 vision per ward).",
        "tiers": {
            "T1": {"main_wards": 3, "sub_wards": 2},
            "T2": {"main_wards": 2, "sub_wards": 1},
            "T3": {"main_wards": 1, "sub_wards": 0}
        },
        "sub_attenuation": "specific",
        "main_only": False
    },
    "CAT-11": {
        "name": "Ranged",
        "description": "Meningkatkan jarak tembak senjata ranged sebesar +1 region dan meningkatkan damage senjata ranged. Memblokir serangan melee dan serangan di satu region yang sama. Sub pack menambah biaya +1 EP.",
        "tiers": {
            "T1": {"range_bonus": 1, "dmg_bonus": 0.15},
            "T2": {"range_bonus": 1, "dmg_bonus": 0.10},
            "T3": {"range_bonus": 1, "dmg_bonus": 0.05}
        },
        "sub_attenuation": "extra_ep_cost",
        "main_only": False
    },
    "CAT-12": {
        "name": "Sword Master",
        "description": "Memblokir penggunaan senjata ranged. Mengabaikan serangan jarak jauh musuh dari jarak jauh (1+ hop). Memperkuat ATK item relic.",
        "tiers": {
            "T1": {"relic_item_atk_mult": 1.00, "ignore_range_hops": 1},
            "T2": {"relic_item_atk_mult": 0.75, "ignore_range_hops": 1},
            "T3": {"relic_item_atk_mult": 0.50, "ignore_range_hops": 1}
        },
        "sub_attenuation": {"relic_mult_factor": 0.5, "ignore_range_hops_sub": 2},
        "main_only": False
    },
    "CAT-13": {
        "name": "Duelist",
        "description": "Mendapatkan bonus statistik ATK dan DEF dari relic saat berduel satu-lawan-satu dengan musuh.",
        "tiers": {
            "T1": {"relic_stat_multiplier": 0.9},
            "T2": {"relic_stat_multiplier": 0.7},
            "T3": {"relic_stat_multiplier": 0.5}
        },
        "sub_attenuation": 0.5,
        "main_only": False
    },
    "CAT-14": {
        "name": "Raider",
        "description": "Hanya aktif untuk Tier 1 (T1). Serangan berhasil akan mencuri 1 slot inventaris musuh. Memblokir pengambilan barang drop di tanah. Sub pack menambah biaya +1 EP ekstra.",
        "tiers": {
            "T1": {"enabled": True},
            "T2": {"enabled": False},
            "T3": {"enabled": False}
        },
        "sub_attenuation": "extra_ep_cost",
        "main_only": False
    },
    "CAT-15": {
        "name": "Last Stand",
        "description": "Satu kali per game: Menolak kematian dan bertahan hidup di HP 1, lalu masuk ke mode berserk dengan HP regenerasi masif dan ATK berlipat ganda berdasarkan tingkat pemulihan.",
        "tiers": {
            "T1": {"berserk_turns": 3, "hp_regen_boost": 5.0, "atk_boost_from_regen": 10.0},
            "T2": {"berserk_turns": 2, "hp_regen_boost": 4.0, "atk_boost_from_regen": 10.0},
            "T3": {"berserk_turns": 1, "hp_regen_boost": 3.0, "atk_boost_from_regen": 10.0}
        },
        "sub_attenuation": {"berserk_turns": 1},
        "main_only": False
    },
    "CAT-16": {
        "name": "Iron Heart",
        "description": "Setiap kali menyerang, secara permanen meningkatkan HP maksimal dasar dan pertahanan dasar (DEF cap 10). Sedikit mengurangi damage yang dihasilkan.",
        "tiers": {
            "T1": {"max_hp_gain": 5, "def_gain": 1, "damage_multiplier": 0.9},
            "T2": {"max_hp_gain": 3, "def_gain": 1, "damage_multiplier": 0.8},
            "T3": {"max_hp_gain": 1, "def_gain": 1, "damage_multiplier": 0.7}
        },
        "sub_attenuation": "stack_bonus_halved",
        "main_only": False
    },
    "CAT-17": {
        "name": "Sunflame Cloak",
        "description": "Membakar musuh di sekitar setiap pergantian giliran berdasarkan nilai HP maksimum dan DEF. Mengurangi damage serangan langsung kita.",
        "tiers": {
            "T1": {"aura_radius": 1, "damage_factor": 1.0, "combat_dmg_mult": 0.65},
            "T2": {"aura_radius": 1, "damage_factor": 0.8, "combat_dmg_mult": 0.55},
            "T3": {"aura_radius": 0, "damage_factor": 0.6, "combat_dmg_mult": 0.45}
        },
        "sub_attenuation": "aura_damage_halved",
        "main_only": False
    },
    "CAT-18": {
        "name": "Assassin",
        "description": "Hanya dapat digunakan di slot Main. Memberikan status stealth (tidak terlihat) dan bonus damage kejutan jika menyerang dari persembunyian. Menyerang akan membatalkan status stealth selama 2 turn.",
        "tiers": {
            "T1": {"expose_vision_threshold": 3, "bonus_dmg_mult": 0.6},
            "T2": {"expose_vision_threshold": 2, "bonus_dmg_mult": 0.5},
            "T3": {"expose_vision_threshold": 1, "bonus_dmg_mult": 0.4}
        },
        "sub_attenuation": None,
        "main_only": True
    },
    "CAT-19": {
        "name": "Pickpocket",
        "description": "Mencuri sMoltz dari musuh saat melewatinya. Sub pack menambah biaya pergerakan sebesar +1 EP.",
        "tiers": {
            "T1": {"steal_limit": 3},
            "T2": {"steal_limit": 2},
            "T3": {"steal_limit": 1}
        },
        "sub_attenuation": "move_cost_increase_1_ep",
        "main_only": False
    }
}