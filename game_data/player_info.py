# game_data/player_info.py

BASE_STATS = {
    "hp": 100,            # HP bawaan agen di awal permainan
    "max_hp": 100,        # Batas HP maksimal dasar
    "ep": 10,             # EP bawaan agen di awal permainan
    "max_ep": 10,         # Batas EP maksimal dasar
    "ep_regen": 1,        # Pemulihan EP bawaan setiap pergantian turn (+1 EP/turn)
    "atk": 25,            # Nilai serangan dasar tanpa senjata (Fist)
    "def": 5,             # Nilai pertahanan dasar tanpa armor
    "vision": 1           # Jarak pandang dasar agen (dalam hitungan region)
}

# Batasan jumlah item maksimal yang dapat dibawa oleh agen di dalam tas
INVENTORY_LIMIT = 10      # Jika tas penuh (jumlah item = 10), aksi 'pickup' akan gagal secara sistem