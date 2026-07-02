from ai.detector.zone_detector import (
    detect_terrain,
    detect_facility,
    detect_weather,
    analyze_visible_world
)
from ai.detector.dead_zone_detector import (
    is_dead_zone,
    is_pending_dead_zone,
    analyze_death_zones,
    get_damage_per_second,
    is_interact_restricted
)
from ai.detector.ground_detector import (
    detect_ground_loot,
    has_loot_on_ground
)
from ai.detector.enemy_detector import (
    calculate_region_layers,
    get_visible_enemies_by_layer,
    get_detailed_enemy_stats
)