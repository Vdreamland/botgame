# -*- coding: utf-8 -*-
"""
ClawRoyale official game constants and physics constraints.
Derived from GitHub master specifications (Pre-Season 1 / Season 1).
"""

from typing import Dict, Any

# Konstanta Dasar Karakter
BASE_HP_MAX: float = 100.0
BASE_EP_MAX: float = 30.0
BASE_ATK: float = 10.0
BASE_DEF: float = 5.0

# Aturan Jeda Waktu & Cooldown (Detik)
COOLDOWN_ACTION_GROUP: float = 30.0    # Cooldown untuk Move, Explore, Attack, Rest, Interact [12]
HEARTBEAT_INTERVAL: float = 5.0        # Interval detak jantung WS server

# Konstanta Bahaya Dead Zone
DEAD_ZONE_EXPANSION_DAY: int = 2       # Ekspansi dimulai pada Hari ke-2 [14]
DEAD_ZONE_EXPANSION_INTERVAL: int = 3   # Mengembang setiap 3 giliran (turns) [14]
DEAD_ZONE_DAMAGE_PER_SECOND: float = 1.34  # Mengurangi 1.34 HP/detik jika di dalam Dead Zone [14]

# Sistem Alert Gauge (Pre-S1)
ALERT_GAUGE_MAX: int = 10              # Menembus 10 memicu spawn Guardian [10]
ALERT_DECAY_PER_TURN: int = -4         # Berkurang 4 poin per turn [10]
ALERT_EXPLORE_PENALTY: int = 2         # Bertambah 2 poin per aksi explore [10]
ALERT_CLEARING_PENALTY: int = 4        # Bertambah 4 poin ekstra saat ruang selesai dibersihkan [10]

# Modifikator Medan (Terrain Types) dan Konsumsi EP
TERRAIN_MODIFIERS: Dict[str, Dict[str, Any]] = {
    "chapel": {"ep_cost_multiplier": 1.0, "def_bonus": 2.0},
    "barn": {"ep_cost_multiplier": 1.0, "def_bonus": 1.0},
    "ruins": {"ep_cost_multiplier": 1.2, "def_bonus": 0.0},
    "glacier": {"ep_cost_multiplier": 1.5, "def_bonus": -1.0},
    "swamp": {"ep_cost_multiplier": 1.8, "def_bonus": -2.0},
    "forest": {"ep_cost_multiplier": 1.1, "def_bonus": 3.0}
}

# Modifikator Cuaca (Weather Status Effects)
WEATHER_EFFECTS: Dict[str, Dict[str, float]] = {
    "sunny": {"atk_multiplier": 1.0, "visibility_radius": 3.0},
    "fog": {"atk_multiplier": 0.8, "visibility_radius": 1.0},
    "rain": {"atk_multiplier": 0.9, "visibility_radius": 2.0},
    "storm": {"atk_multiplier": 0.7, "visibility_radius": 1.0}
}