# game_data/world_info.py

TERRAINS = {
    "plains": {
        "vision_modifier": 1,  # Memperluas jangkauan penglihatan (+1 Vision)
        "extra_ep_cost": 0,    # Biaya pergerakan standar (1 EP)
        "stealth_rating": "poor"
    },
    "forest": {
        "vision_modifier": -1, # Mempersempit jangkauan penglihatan (-1 Vision)
        "extra_ep_cost": 0,
        "stealth_rating": "good"
    },
    "hills": {
        "vision_modifier": 2,  # Memperluas jangkauan penglihatan secara maksimal (+2 Vision)
        "extra_ep_cost": 0,
        "stealth_rating": "poor"
    },
    "ruins": {
        "vision_modifier": 0,
        "extra_ep_cost": 0,
        "stealth_rating": "medium"
    },
    "water": {
        "vision_modifier": 0,
        "extra_ep_cost": 1,    # Melangkah ke air memakan total 2 EP (1 standard + 1 extra)
        "stealth_rating": "poor"
    }
}

WEATHERS = {
    "clear": {
        "vision_modifier": 0,
        "combat_modifier": 0.00 # Tidak ada pengurangan performa pertarungan
    },
    "rain": {
        "vision_modifier": -1,
        "combat_modifier": -0.05 # Pengurangan performa pertarungan sebesar -5%
    },
    "fog": {
        "vision_modifier": -2,
        "combat_modifier": -0.10 # Pengurangan performa pertarungan sebesar -10%
    },
    "storm": {
        "vision_modifier": -2,
        "combat_modifier": -0.15 # Pengurangan performa pertarungan sebesar -15%
    }
}

# Diubah agar mencocokkan string payload 'facility' dari API game asli (Supply Cache)
FACILITIES = {
    "Broadcast Station": "Aksi broadcast dapat dipanggil secara bebas tanpa Megaphone.",
    "Supply Cache": "Berisi peti pasokan (Cache) yang menjatuhkan item acak saat dibuka.",
    "Medical Facility": "Memulihkan HP karakter secara instan.",
    "Watchtower": "Meningkatkan jangkauan penglihatan karakter secara temporer (+2 vision).",
    "Cave": "Agen masuk ke dalam goa (cave_in/cave_out). Vision berkurang -2, req +2, dan agen tidak bisa melangkah keluar wilayah."
}

DEATH_ZONE = {
    "start_day": 2,            # Zona kematian mulai menyusut dari ujung luar peta pada hari ke-2
    "expansion_interval_turns": 3, # Berpindah menyusut setiap 3 turn (18 jam waktu dalam game)
    "damage_per_second": 1.34, # Mengakibatkan pengurangan HP sebesar 1.34 HP/detik jika berdiri di dalamnya
    "action_restrictions": {
        "interact": False      # Memanggil aksi 'interact' di wilayah Death Zone dilarang keras (error)
    }
}

# Representasi Sistem Waktu Permainan (60 Turn total, berakhir hari ke-16)
TIME_SYSTEM = {
    "turn_duration_hours": 6,  # 1 turn mewakili 6 jam di dalam game (30 detik real-time)
    "day_hours": {
        "start": 6,            # Siang hari: pukul 06:00 s.d 18:00 (2 turns)
        "end": 18
    },
    "night_hours": {
        "start": 18,           # Malam hari: pukul 18:00 s.d 06:00 (2 turns)
        "end": 6
    }
}