# struktur project 

botgame/
├── .env                                      # Kredensial rahasia (Global API Keys & Private Keys)
├── config_agents.json                        # Konfigurasi instansi akun-akun bot (Termasuk parameter "room_preference")
│
├── config/                                   # LAPISAN KONFIGURASI STATIS
│   ├── settings.py                           # Ambang batas risiko HP, EP, & toleransi alert gauge
│   ├── game_constants.py                     # Nilai konstanta medan, cuaca, rate limit, & cooldown
│   └── item_registry.py                      # Kamus data tipe senjata, armor, consumables, & relic
│
├── core/                                     # LAPISAN LIFECYCLE, INTEGRASI, & JARINGAN
│   ├── agent_instance.py                     # Kelas utama pembungkus loop game satu akun bot
│   │
│   ├── lifecycle/                            # A. Sub-Modul Alur Hidup Agen
│   │   ├── state_router.py                   # State Router resmi (NO_ACCOUNT, READY, IN_GAME, ERROR)
│   │   ├── setup_handler.py                  # Pendaftaran akun, request whitelist, & inisialisasi wallet
│   │   ├── onboarding_redeemer.py            # Otomatisasi klaim kode 'WELCOME' via POST /api/redeem
│   │   ├── wallet_policy.py                  # Validasi primary agent guna menghindari error NOT_PRIMARY_AGENT
│   │   ├── token_registrar.py                # Registrasi token agen khusus untuk Forge (Pre-S1)
│   │   ├── room_selector.py                  # Dynamic Room Selector: Mengatur transisi masuk Free vs Paid room
│   │   └── runtime_manager.py                # Eksekutor runtime loop (Heartbeat Mode vs Autonomous Mode)
│   │
│   ├── network/                              # B. Sub-Modul Jaringan
│   │   ├── api_client.py                     # HTTP client (httpx) untuk REST API
│   │   ├── ws_client.py                      # WebSocket client (websockets) game connection
│   │   └── document_cache.py                 # Mesin sinkronisasi ETag cache dokumen (If-None-Match)
│   │
│   └── state/                                # C. Sub-Modul Game State
│       ├── game_state.py                     # Sinkronisasi posisi koordinat map, sisa giliran, & info terrain
│       ├── team_registry.py                  # Database lokal real-time ID bot kita yang sedang satu arena
│       └── cooldown_manager.py               # Monitor cooldown group aksi 30 detik (canAct=True/False)
│
├── brain/                                    # LAPISAN BRAIN / KEPUTUSAN UTAMA
│   ├── decision_engine.py                    # Evaluator pengambilan tindakan berbasis utilitas scoring
│   └── memory/                               # Sub-Modul Pembelajaran & Memori
│       └── cross_game_memory.py              # Pengelola file context.json untuk optimalisasi taktik bot
│
├── strategies/                               # LAPISAN MODUL STRATEGI MANDIRI
│   ├── scanners/
│   │   ├── enemy_scanner.py                  # Deteksi musuh (Melewati filter sekutu agar tidak menyerang tim sendiri)
│   │   ├── enemy_stats_scanner.py            # Deteksi sisa HP, EP, & buff/debuff target musuh
│   │   ├── enemy_gear_scanner.py             # Deteksi persenjataan & status bonus "fullSet" musuh
│   │   └── ground_item_scanner.py            # Deteksi item di tanah (koordinat, tier, tipe)
│   ├── team/
│   │   └── team_coordinator.py               # Logika sharing target, koordinasi posisi, menghindari friendly fire
│   ├── combat/
│   │   ├── battle_analyzer.py                # Evaluasi ancaman lawan di radius koordinat bot
│   │   ├── victory_calculator.py             # Matematika simulasi peluang menang bertarung (Win Rate %)
│   │   ├── engagement_controller.py          # Kontrol jarak serang optimal (melee 0 vs ranged 1-2)
│   │   └── cooldown_tracker.py               # Pelacak sisa EP & ketersediaan cooldown aksi musuh
│   ├── hunter/
│   │   └── hunter_mode_controller.py         # Kriteria aktivasi mode berburu agresif & target lock
│   ├── movement/
│   │   ├── pathfinder.py                     # Navigasi heksagonal A* menghindari obstacle & hazard
│   │   └── chase_tactics.py                  # Manuver taktis pencegatan rute musuh
│   ├── recovery/
│   │   ├── health_restorer.py                # Logika efisiensi konsumsi item medis (Bandage, Medkit)
│   │   └── energy_manager.py                 # Logika pengisian EP (rest) di lokasi aman
│   ├── environmental/
│   │   └── weather_terrain_handler.py        # Penyesuaian gerak & EP berdasarkan cuaca/terrain
│   ├── inventory/
│   │   ├── equip_selector.py                 # Pemasangan perlengkapan untuk bonus "fullSet" wajib
│   │   └── inventory_manager.py              # Pemilahan barang bawaan (buang/ambil/ekspansi slot)
│   ├── exploration/
│   │   └── ruin_explorer.py                  # Navigasi ruin & memantau alert gauge agar tidak menyentuh 10
│   ├── lobby/
│   │   ├── reforge_optimizer.py              # Otomatisasi proses reforge relic mencari stat ideal di lobby
│   │   └── shop_manager.py                   # Belanja otomatis gacha ticket & expand inventory via Moltz
│   ├── phases/
│   │   ├── early_game_strategy.py            # Fokus: Lengkapi RGB "fullSet", kumpulkan resource, hindari PVP
│   │   ├── mid_game_strategy.py              # Fokus: Kuasai ruin, optimasi gear, eliminasi target lemah
│   │   └── late_game_strategy.py             # Fokus: Survival di zona sempit, amankan posisi pusat, hemat EP
│   └── hazard/
│       ├── deadzone_warning_handler.py       # Antisipasi: Evakuasi dini saat Dead Zone akan meluas (Day 2)
│       └── deadzone_active_handler.py        # Darurat: Evakuasi cepat & auto-healing di dalam kabut gas (1.34 HP/s)
│
├── actions/                                  # LAPISAN FORMULASI PAYLOAD PERINTAH
│   ├── action_dispatcher.py                  # Pengirim payload JSON akhir ke WebSocket
│   ├── cooldown_actions.py                   # Format perintah ber-cooldown (Move, Explore, Attack, Rest, dll.)
│   └── free_actions.py                       # Format perintah bebas cooldown (Equip, Pickup, Whisper, Broadcast)
│
├── ui/                                       # LAPISAN VISUALISASI TERMINAL (TUI)
│   ├── terminal_dashboard.py                 # Panel dashboard PowerShell/CMD memantau seluruh bot aktif (rich)
│   └── ascii_map_renderer.py                 # Penggambar visual map heksagonal mini menggunakan karakter teks
│
├── logs/                                     # LAPISAN LOGGING AUDIT (DIREKTORI BERKAS TEKS)
│   ├── bot_alice.log                         # Log audit khusus aktivitas akun Bot Alice
│   ├── bot_bob.log                           # Log audit khusus aktivitas akun Bot Bob
│   └── system.log                            # Log aktivitas crash sistem global / error jaringan
│
├── utils/                                    # LAPISAN UTILITY HELPER
│   ├── crypto_helper.py                      # Kriptografi penandatanganan pesan EIP-712 & penanganan kunci
│   ├── math_helper.py                        # Kalkulator jarak koordinat & penskalaan skor utilitas
│   ├── rate_limiter.py                       # (NEW) Pengendali batas API (REST & WS) agar tidak diblokir server
│   └── logger.py                             # Generator format logging rapi & aman
│
├── orchestrator.py                           # Manajer Pusat: Spawning & koordinasi multi-bot asinkron
├── skill.md                                  # Dokumen panduan resmi & manifest prompt AI dari developer
└── index.py                                  # Entry Point Utama (Python Bootstrap)

# Dokumentasi resmi
PlayGuide : https://www.clawroyale.ai/guide
GameGuide : https://www.clawroyale.ai/game-guide
Documentation : https://www.clawroyale.ai/docs
PreSesion Guide : https://www.clawroyale.ai/pack-catalog
Patch Notes : https://www.clawroyale.ai/news?filter=patch_note
For AI Agents / Moltbot / Clawdbot / OpenClawbot : https://github.com/Vdreamland/botgame/blob/master/skill.md



Link url github

botgame/

.env
config_agents.json

config >
settings.py
game_constants.py
item_registry.py

core >
agent_instance.py

core > lifecycle >
state_router.py
setup_handler.py
onboarding_redeemer.py
wallet_policy.py
token_registrar.py
room_selector.py
runtime_manager.py

core > network >
api_client.py
ws_client.py
document_cache.py

core > state >
game_state.py
team_registry.py
cooldown_manager.py

brain >
decision_engine.py

brain > memory >
cross_game_memory.py

strategies >

strategies > scanners >
enemy_scanner.py
enemy_stats_scanner.py
enemy_gear_scanner.py
ground_item_scanner.py

strategies > team >
team_coordinator.py

strategies > combat >
battle_analyzer.py
victory_calculator.py
engagement_controller.py
cooldown_tracker.py

strategies > hunter >
hunter_mode_controller.py

strategies > movement >
pathfinder.py
chase_tactics.py

strategies > recovery >
health_restorer.py
energy_manager.py

strategies > environmental >
weather_terrain_handler.py

strategies > inventory >
equip_selector.py
inventory_manager.py

strategies > exploration >
ruin_explorer.py

strategies > lobby >
reforge_optimizer.py
shop_manager.py

strategies > phases >
early_game_strategy.py
mid_game_strategy.py
late_game_strategy.py

strategies > hazard >
deadzone_warning_handler.py
deadzone_active_handler.py

actions >
action_dispatcher.py
cooldown_actions.py
free_actions.py

ui >
terminal_dashboard.py
ascii_map_renderer.py

logs >
bot_alice.log
bot_bob.log
system.log

utils >
crypto_helper.py
math_helper.py
rate_limiter.py
logger.py

orchestrator.py
skill.md
index.py


