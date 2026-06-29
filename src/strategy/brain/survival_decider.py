import random
from typing import Dict, Any, Optional
from src.strategy.brain.game_context import GameContext
from src.strategy.brain.base_decider import BaseDecider
from src.strategy.behaviors.utility_behavior import UtilityBehavior

class SurvivalDecider(BaseDecider):
    
    def decide(self, view: Dict[str, Any], context: GameContext) -> Optional[Dict[str, Any]]:
        view_self = view.get("self", {})
        self_id = view_self.get("id", "")
        hp = view_self.get("hp", 100)
        ep = view_self.get("ep", 10)
        inventory = view_self.get("inventory", [])
        current_region = view.get("currentRegion", {})
        region_id = current_region.get("id")
        is_active_deathzone = current_region.get("isDeathZone", False)

        # PRIORITAS 1: LARI MUTLAK JIKA BERADA DI DEATH ZONE AKTIF
        if is_active_deathzone:
            connections = current_region.get("connections", [])
            safe_options = [
                r_id for r_id in connections 
                if r_id not in context.pending_deathzones and r_id not in context.active_deathzones
            ]
            pending_options = [
                r_id for r_id in connections 
                if r_id not in context.active_deathzones
            ]
            chosen_target = None
            if safe_options:
                chosen_target = random.choice(safe_options)
            elif pending_options:
                chosen_target = random.choice(pending_options)
            elif connections:
                chosen_target = random.choice(connections)

            if chosen_target:
                context.last_action_type = "move"
                target_name = context.region_names.get(chosen_target, f"Hex-{chosen_target[:8]}")
                return UtilityBehavior.build_move_action(
                    region_id=chosen_target,
                    thought=f"Standing in ACTIVE deathzone. Fleeing immediately to: {target_name}"
                )

        # PRIORITAS 2: LARI DARI ANCAMAN TEMPUR AKTIF (HP < 60 & Ada musuh berdiri di wilayah yang sama!)
        # Jangan gunakan obat atau diam di tempat jika sedang digebuki musuh. Kabur dahulu, sembuhkan kemudian!
        visible_agents = view.get("visibleAgents", [])
        enemies_here = [a for a in visible_agents if a.get("id") != self_id and a.get("regionId") == region_id and a.get("isAlive", True)]
        
        if hp < 60 and enemies_here:
            connections = current_region.get("connections", [])
            safe_options = [
                r_id for r_id in connections 
                if r_id not in context.pending_deathzones and r_id not in context.active_deathzones
            ]
            pending_options = [
                r_id for r_id in connections 
                if r_id not in context.active_deathzones
            ]
            chosen_target = None
            if safe_options:
                chosen_target = random.choice(safe_options)
            elif pending_options:
                chosen_target = random.choice(pending_options)
            elif connections:
                chosen_target = random.choice(connections)

            if chosen_target:
                context.last_action_type = "move"
                target_name = context.region_names.get(chosen_target, f"Hex-{chosen_target[:8]}")
                return UtilityBehavior.build_move_action(
                    region_id=chosen_target,
                    thought=f"Under threat ({hp}/100) with {len(enemies_here)} enemies. Fleeing to safe region: {target_name}"
                )

        # PRIORITAS 3: PEMULIHAN HP DARURAT (Hanya dievaluasi jika berada di koordinat aman dari musuh langsung)
        if hp < 50:
            for item in inventory:
                if isinstance(item, dict):
                    item_name = item.get("name") or item.get("displayName") or ""
                    item_id = item.get("id", "")
                    if item_name in ["Medkit", "Emergency Food", "Bandage"] and item_id:
                        context.last_action_type = "use_item"
                        return UtilityBehavior.build_use_item_action(
                            item_id=item_id,
                            thought=f"HP critical ({hp}/100) in safe zone. Consuming {item_name} to heal."
                        )

        # PRIORITAS 4: PEMULIHAN EP DARURAT (Hanya dievaluasi jika berada di koordinat aman dari musuh langsung)
        if ep < 2:
            for item in inventory:
                if isinstance(item, dict):
                    item_name = item.get("name") or item.get("displayName") or ""
                    item_id = item.get("id", "")
                    if item_name in ["Energy Drink", "Medkit"] and item_id:
                        context.last_action_type = "use_item"
                        return UtilityBehavior.build_use_item_action(
                            item_id=item_id,
                            thought=f"Energy critical ({ep}/10) in safe zone. Consuming {item_name} to recover EP."
                        )

        # PRIORITAS 5: FASILITAS MEDIS (Hanya dievaluasi jika berada di koordinat aman dari musuh langsung)
        if hp < 70:
            already_interacted = any(
                act.get("type") == "interact" and act.get("regionId") == region_id 
                for act in context.history_actions
            )
            if not already_interacted:
                interactables = current_region.get("interactables", [])
                for fac in interactables:
                    if isinstance(fac, dict):
                        fac_name = fac.get("name", "")
                        is_used = fac.get("isUsed", True)
                        if fac_name == "Medical Facility" and not is_used:
                            context.last_action_type = "interact"
                            context.history_actions.append({"type": "interact", "regionId": region_id})
                            return UtilityBehavior.build_interact_action(
                                thought="HP is low. Interacting with Medical Facility to heal."
                            )

        # PRIORITAS 6: MENGHINDARI PENDING DEATH ZONE
        in_danger_zone = (region_id in context.pending_deathzones)
        if in_danger_zone or (hp < 40 and enemies_here):
            connections = current_region.get("connections", [])
            safe_options = [
                r_id for r_id in connections 
                if r_id not in context.pending_deathzones and r_id not in context.active_deathzones
            ]
            pending_options = [
                r_id for r_id in connections 
                if r_id not in context.active_deathzones
            ]
            chosen_target = None
            if safe_options:
                chosen_target = random.choice(safe_options)
            elif pending_options:
                chosen_target = random.choice(pending_options)
            elif connections:
                chosen_target = random.choice(connections)

            if chosen_target:
                context.last_action_type = "move"
                target_name = context.region_names.get(chosen_target, f"Hex-{chosen_target[:8]}")
                return UtilityBehavior.build_move_action(
                    region_id=chosen_target,
                    thought=f"HP low or Zone shrinking. Escaping to adjacent safe region: {target_name}"
                )

        return None