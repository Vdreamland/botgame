# -*- coding: utf-8 -*-
"""
ClawRoyale Agent settings configuration.
Defines tactical decision limits and safety thresholds for the AI engine [11].
"""

from typing import Dict, Any

AI_SETTINGS: Dict[str, Any] = {
    "hp_panic_threshold": 0.35,
    "hp_secure_threshold": 0.80,
    
    # Penyesuaian ambang batas EP agar sinkron dengan kapasitas maksimal 10.0 EP [11]
    "ep_minimum_reserve": 3.0,
    "ep_optimal_reserve": 8.0,
    
    "alert_gauge_panic": 8,
    "alert_gauge_safe": 4,
    
    "min_win_rate_for_aggression": 0.75,
    "flee_win_rate_threshold": 0.40,
    
    "scan_radius_enemies": 3,
    "scan_radius_items": 2,
    
    "ws_max_messages_per_minute": 110,
    "rest_max_calls_per_minute": 280
}