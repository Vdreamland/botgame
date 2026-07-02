# game_data/action_info.py

# Daftar seluruh aksi game beserta aturan sistemnya
ACTIONS = {
    "move": {
        "ep_cost": 1,          # Naik menjadi 2 EP jika melangkah ke wilayah terrain 'water'
        "has_cooldown": True,  # Memicu canAct = false selama 30 detik
        "requires_target": True
    },
    "explore": {
        "ep_cost": 1,
        "has_cooldown": True,
        "requires_target": False
    },
    "attack": {
        "ep_cost": "variable", # Mengikuti nilai ep_cost yang ditentukan di dalam weapon_info.py
        "has_cooldown": True,
        "requires_target": True
    },
    "use_item": {
        "ep_cost": 0,
        "has_cooldown": True,
        "requires_target": True
    },
    "interact": {
        "ep_cost": 0,
        "has_cooldown": True,
        "requires_target": True,
        "forbidden_in_deathzone": True # Pemanggilan aksi 'interact' akan diblokir total jika agen berada di dalam Death Zone
    },
    "rest": {
        "ep_cost": 0,
        "has_cooldown": True,
        "requires_target": False
    },
    "pickup": {
        "ep_cost": 0,
        "has_cooldown": False, # Aksi bebas (Free Action): dapat dipanggil beruntun tanpa cooldown 30 detik
        "requires_target": True
    },
    "equip": {
        "ep_cost": 0,
        "has_cooldown": False,
        "requires_target": True
    },
    "talk": {
        "ep_cost": 0,
        "has_cooldown": False,
        "requires_target": False
    },
    "whisper": {
        "ep_cost": 0,
        "has_cooldown": False,
        "requires_target": True
    },
    "broadcast": {
        "ep_cost": 0,
        "has_cooldown": False,
        "requires_target": False
    }
}

# Konstanta Pengaturan Sistem Alert Gauge
ALERT_SYSTEM = {
    "max_gauge": 10,           # Batas maksimum nilai gauge sebelum status alert aktif
    "explore_charge": 2,       # Setiap pemanggilan aksi 'explore' menambah +2 pada Alert Gauge agen
    "ruin_clear_bonus": 4,     # Jika aksi eksplorasi berhasil mengosongkan reruntuhan, ditambahkan +4 ekstra
    "turn_decay": -4,          # Nilai Alert Gauge luruh sebesar -4 pada setiap akhir giliran saat alert aktif
}

# Pembatasan Pesan Teks Chat
MAX_CHAT_LENGTH = 200          # Maksimal karakter teks untuk aksi talk, whisper, dan broadcast