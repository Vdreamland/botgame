# -*- coding: utf-8 -*-
"""
ClawRoyale Agent settings configuration.
Defines tactical decision limits and safety thresholds for the AI engine.
"""

from typing import Dict, Any

AI_SETTINGS: Dict[str, Any] = {
    # Ambang batas kesehatan (HP) dalam persen (0.0 - 1.0)
    "hp_panic_threshold": 0.35,       # HP di bawah 35%: paksa lari / cari healing
    "hp_secure_threshold": 0.80,      # HP di atas 80%: dinilai aman untuk bertarung
    
    # Ambang batas energi (EP)
    "ep_minimum_reserve": 5.0,         # Jangan lakukan gerakan taktis jika EP < 5
    "ep_optimal_reserve": 20.0,        # Batas EP aman untuk mulai mode pemburu (hunting)
    
    # Toleransi Ancaman Alert Gauge (0 - 10)
    "alert_gauge_panic": 8,            # Jangan lakukan explore jika alert gauge >= 8
    "alert_gauge_safe": 4,             # Aman untuk explore jika alert gauge <= 4
    
    # Batas Toleransi Peluang Kemenangan (0.0 - 1.0)
    "min_win_rate_for_aggression": 0.75,  # Hanya serang musuh jika Win Rate perkiraan >= 75%
    "flee_win_rate_threshold": 0.40,       # Kabur seketika jika Win Rate perkiraan < 40%
    
    # Jangkauan Pemindaian Visual Map (Radius Hex)
    "scan_radius_enemies": 3,
    "scan_radius_items": 2,
    
    # Pengaturan Rate Limiting Internal
    "ws_max_messages_per_minute": 110,   # Batas aman di bawah aturan resmi 120 msg/min
    "rest_max_calls_per_minute": 280     # Batas aman gabungan di bawah aturan resmi 300 calls/min
}