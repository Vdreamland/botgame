import random
from typing import Dict, Any, Optional
from src.strategy.brain.game_context import GameContext
from src.strategy.brain.base_decider import BaseDecider
from src.strategy.behaviors.utility_behavior import UtilityBehavior
from src.strategy.navigation.pathfinder import Pathfinder
from config import settings

class IdleDecider(BaseDecider):
    
    def decide(self, view: Dict[str, Any], context: GameContext) -> Optional[Dict[str, Any]]:
        view_self = view.get("self", {})
        bot_name = view_self.get("name", "")
        hp = view_self.get("hp", 100)
        ep = view_self.get("ep", 10)
        kills = view_self.get("kills", 0)
        current_turn = view.get("turn", 0)
        
        current_region = view.get("currentRegion", {})
        current_region_id = current_region.get("id")
        
        # Ekstraksi tipe cuaca real-time dari view
        weather_type = view.get("weather") or current_region.get("weather") or "clear"
        
        # 1. PLAYER KILLS RECORDING
        if kills > context.last_kills_count:
            context.last_kills_count = kills
            if context.last_attack_region and context.last_attack_region not in settings.SHARED_LOOT_TARGETS:
                settings.SHARED_LOOT_TARGETS.append(context.last_attack_region)
            
        # 2. MONSTER KILLS RECORDING
        if context.last_action_type == "attack" and context.last_attack_region:
            opponents_now = context.opponents_data.get("players", []) + context.opponents_data.get("monsters", [])
            opponents_still_in_target_region = any(
                opp.get("region_id") == context.last_attack_region for opp in opponents_now
            )
            if not opponents_still_in_target_region:
                if context.last_attack_region not in settings.SHARED_LOOT_TARGETS:
                    settings.SHARED_LOOT_TARGETS.append(context.last_attack_region)
                context.last_attack_region = ""

                connections = current_region.get("connections", [])
                
        connections = current_region.get("connections", [])
        if not connections:
            return None

        # Clean all SOS signals at this region
        while current_region_id in settings.SOS_TARGETS:
            settings.SOS_TARGETS.remove(current_region_id)

        # Clean all Shared Loot targets at this region
        while current_region_id in settings.SHARED_LOOT_TARGETS:
            settings.SHARED_LOOT_TARGETS.remove(current_region_id)

        # PRIORITY 1: RESPOND TO ALLY SOS CALLS
        if hp >= 60 and settings.SOS_TARGETS:
            target_region_id = settings.SOS_TARGETS[0]
            path = Pathfinder.find_shortest_path(
                start_id=current_region_id, 
                target_id=target_region_id, 
                context=context, 
                weather_type=weather_type
            )
            if path and len(path) >= 2:
                next_step_id = path[1]
                context.last_action_type = "move"
                target_name = context.region_names.get(target_region_id, f"Hex-{target_region_id[:8]}")
                return UtilityBehavior.build_move_action(
                    region_id=next_step_id,
                    thought=f"Ally under threat! Navigating to backup site: {target_name}."
                )
            else:
                if settings.SOS_TARGETS:
                    settings.SOS_TARGETS.pop(0)

        # PRIORITY 2: COOPERATIVE LOOT HARVESTING
        if settings.SHARED_LOOT_TARGETS:
            target_region_id = settings.SHARED_LOOT_TARGETS[0]
            path = Pathfinder.find_shortest_path(
                start_id=current_region_id, 
                target_id=target_region_id, 
                context=context, 
                weather_type=weather_type
            )
            if path and len(path) >= 2:
                next_step_id = path[1]
                context.last_action_type = "move"
                target_name = context.region_names.get(target_region_id, f"Hex-{target_region_id[:8]}")
                return UtilityBehavior.build_move_action(
                    region_id=next_step_id,
                    thought=f"Matchmaking loot target confirmed. Navigating to secured kill site: {target_name}."
                )
            else:
                if settings.SHARED_LOOT_TARGETS:
                    settings.SHARED_LOOT_TARGETS.pop(0)

        # PRIORITY 3: SQUAD FOLLOWER LOGIC (Regroup)
        leader_name = settings.ALLY_NAMES[0] if settings.ALLY_NAMES else ""
        if bot_name and leader_name and bot_name != leader_name:
            leader_pos = settings.BOT_POSITIONS.get(leader_name)
            if leader_pos and leader_pos != current_region_id:
                path = Pathfinder.find_shortest_path(
                    start_id=current_region_id, 
                    target_id=leader_pos, 
                    context=context, 
                    weather_type=weather_type
                )
                if path and len(path) >= 2:
                    next_step_id = path[1]
                    context.last_action_type = "move"
                    target_name = context.region_names.get(leader_pos, f"Hex-{leader_pos[:8]}")
                    return UtilityBehavior.build_move_action(
                        region_id=next_step_id,
                        thought=f"Squad tactic: Regrouping with leader {leader_name}."
                    )
            
        safe_connections = [
            r_id for r_id in connections 
            if r_id not in context.pending_deathzones 
            and r_id not in context.active_deathzones
            and r_id not in settings.SHARED_ACTIVE_DEATHZONES
        ]
        
        if current_turn > 15 and safe_connections:
            safe_non_corners = [
                r_id for r_id in safe_connections
                if len(context.map_graph.get(r_id, [1, 2, 3, 4])) > 3
            ]
            if safe_non_corners:
                safe_connections = safe_non_corners
        else:
            safe_non_corners = [
                r_id for r_id in safe_connections
                if len(context.map_graph.get(r_id, [1, 2, 3, 4])) > 3
            ]
        
        pending_connections = [
            r_id for r_id in connections 
            if r_id not in context.active_deathzones
            and r_id not in settings.SHARED_ACTIVE_DEATHZONES
        ]
        
        if safe_non_corners and current_turn <= 15:
            chosen_connections = safe_non_corners
        else:
            chosen_connections = safe_connections if safe_connections else (pending_connections if pending_connections else connections)
        
        if chosen_connections:
            unvisited = [r_id for r_id in chosen_connections if r_id not in settings.SHARED_VISITED_HISTORY]
            final_options = unvisited if unvisited else chosen_connections
            
            has_healing = False
            for item in view_self.get("inventory", []):
                if isinstance(item, dict):
                    item_name = item.get("name") or item.get("displayName") or ""
                else:
                    item_name = str(item)
                if item_name in ["Medkit", "Emergency Food", "Bandage"]:
                    has_healing = True
                    break
            
            if hp < 40 and not has_healing:
                occupied_regions = set()
                for p in context.opponents_data.get("players", []):
                    occupied_regions.add(p.get("region_id"))
                for m in context.opponents_data.get("monsters", []):
                    occupied_regions.add(m.get("region_id"))
                
                safe_from_enemies = [r_id for r_id in final_options if r_id not in occupied_regions]
                if safe_from_enemies:
                    final_options = safe_from_enemies

            target_region_id = random.choice(final_options)
            context.last_action_type = "move"
            
            target_name = context.region_names.get(target_region_id, f"Hex-{target_region_id[:8]}")
            return UtilityBehavior.build_move_action(
                region_id=target_region_id, 
                thought=f"Exploring adjacent region: {target_name}"
            )
            
        return None