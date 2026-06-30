from typing import Dict, Any, Optional, List
from config import settings
from src.strategy.behaviors.utility_behavior import UtilityBehavior

def evaluate_adjacent_looting(
    hp: int, 
    valid_targets: List[Dict[str, Any]], 
    connections: List[str], 
    context: Any
) -> Optional[Dict[str, Any]]:
    """Mengevaluasi taktik menjarah sMoltz di ubin tetangga selama pertempuran menggunakan sistem Threat-Aware HP."""
    # 1. Pastikan tidak ada ancaman jarak dekat di ubin tempat kita berdiri (Layer 0 kosong)
    no_enemies_here = not any(opp["distance"] == 0 for opp in valid_targets)
    if not no_enemies_here:
        return None

    # 2. Ukur kedekatan ancaman (apakah ada musuh di Layer 1 / adjacent)
    has_close_threats = any(opp["distance"] <= 1 for opp in valid_targets)
    
    # Formula Threat-Aware: Butuh HP >= 60 jika musuh dekat, atau HP >= 40 jika musuh jauh
    required_hp = 60 if has_close_threats else 40
    
    if hp >= required_hp and settings.SHARED_LOOT_TARGETS:
        adjacent_loot_region = None
        for loot_r in settings.SHARED_LOOT_TARGETS:
            if loot_r in connections:
                adjacent_loot_region = loot_r
                break
                
        if adjacent_loot_region:
            context.last_action_type = "move"
            target_name = context.region_names.get(adjacent_loot_region, f"Hex-{adjacent_loot_region[:8]}")
            return UtilityBehavior.build_move_action(
                region_id=adjacent_loot_region,
                thought=f"Tactical looting (Threat-Aware): HP {hp}/{required_hp} is safe. Stepping 1-hex to adjacent Secured Kill Site: {target_name} to harvest sMoltz."
            )
            
    return None