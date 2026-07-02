# game_data/monster_info.py

MONSTERS = {
    "Wolf": {
        "hp": 25,
        "atk": 15,
        "def": 1,
        "is_guardian": False
    },
    "Bear": {
        "hp": 30,
        "atk": 12,
        "def": 3,
        "is_guardian": False
    },
    "Bandit": {
        "hp": 40,
        "atk": 25,
        "def": 5,
        "is_guardian": False
    }
}

GUARDIAN_STATS = {
    "hp": 150,
    "atk": 20,
    "def": 34,
    "ep": 10,
    "vision": 1,
    "is_guardian": True,
    "range_bonus": 2,          # Rentang serangan dasar Guardian adalah vision + 2 (ranged attack)
    "is_stationary": True      # Guardian bertindak sebagai Turret diam dan tidak dapat berpindah tempat
}

# Catatan Aturan Khusus Guardian untuk logika AI:
# 1. Guardian hanya menyerang pemain yang berada dalam kondisi Alert Aktif (Alert Gauge mencapai 10).
# 2. Guardian tidak menyerang monster biasa atau Guardian lainnya.
# 3. Target serangan dibatalkan seketika jika Alert Gauge pemain kembali menjadi 0, pemain keluar dari jangkauan, atau mati.
# 4. Di dalam Free Room terdapat 15 Guardian (1 per reruntuhan). Di Paid Room terdapat 8 Guardian.
# 5. Mengalahkan Guardian di Free Room memberikan drop koin sebesar 40 sMoltz langsung di tanah.