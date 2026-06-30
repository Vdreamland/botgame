import random
from typing import Dict, Any, Optional
from src.strategy.brain.game_context import GameContext
from src.strategy.brain.base_decider import BaseDecider
from src.strategy.behaviors.utility_behavior import UtilityBehavior
from config import settings
from src.utils.logger import logger

class SurvivalDecider(BaseDecider):
    
    def decide(self, view: Dict[str, Any], context: GameContext) -> Optional[Dict[str, Any]]:
        view_self = view.get("self", {})
        self_id = view_self.get("id", "")
        bot_name = view_self.get("name", "")  # Mengembalikan inisialisasi bot_name untuk log Deadzone Filter
        hp = view_self.get("hp", 100)
        ep = view_self.get("ep", 10)
        inventory = view_self.get("inventory", [])
        current_region = view.get("currentRegion", {})
        region_id = current_region.get("id")
        is_active_deathzone = current_region.get("isDeathZone", False)
        current_turn = view.get("turn", 0)

        # PRIORITY 1: MELARIKAN DIRI DARI ACTIVE DEATHZONE
        if is_active_deathzone:
            connections = current_region.get("connections", [])
            
            # PETA PENYARINGAN DEADZONE: Mencoret ubin menyusut/aktif dengan mencetak log audit transparan
            safe_options = []
            for r_id in connections:
                if (r_id in context.pending_deathzones) or (r_id in context.active_deathzones) or (r_id in settings.SHARED_ACTIVE_DEATHZONES):
                    rejected_name = context.region_names.get(r_id, f"Hex-{r_id[:8]}")
                    logger.warning(f"[Deadzone Filter] [{bot_name}] Rejecting escape connection: {rejected_name} (Hex-{r_id[:8]}) - DANGEROUS/DEADZONE!")
                else:
                    safe_options.append(r_id)
            
            if current_turn > 15 and safe_options:
                safe_non_corners = [
                    r_id for r_id in safe_options
                    if len(context.map_graph.get(r_id, [1, 2, 3, 4])) > 3
                ]
                if safe_non_corners:
                    safe_options = safe_non_corners

            pending_options = []
            for r_id in connections:
                if (r_id in context.active_deathzones) or (r_id in settings.SHARED_ACTIVE_DEATHZONES):
                    pass
                else:
                    pending_options.append(r_id)
            
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

        enemies_here = [p for p in context.opponents_data.get("players", []) if p.get("region_id") == region_id]
        monsters_here = [m for m in context.opponents_data.get("monsters", []) if m.get("region_id") == region_id]
        threats_here = enemies_here + monsters_here

        # PRIORITY 1.5: OUTNUMBERED ESCAPE (KABUR SAAT KALAH JUMLAH)
        allies_here = sum(1 for name, pos in settings.BOT_POSITIONS.items() if pos == region_id)
        is_outnumbered = len(threats_here) > allies_here
        if is_outnumbered and len(threats_here) >= 2:
            connections = current_region.get("connections", [])
            
            safe_options = []
            for r_id in connections:
                if (r_id in context.pending_deathzones) or (r_id in context.active_deathzones) or (r_id in settings.SHARED_ACTIVE_DEATHZONES):
                    rejected_name = context.region_names.get(r_id, f"Hex-{r_id[:8]}")
                    logger.warning(f"[Deadzone Filter] [{bot_name}] Rejecting escape connection (outnumbered): {rejected_name} (Hex-{r_id[:8]}) - DANGEROUS/DEADZONE!")
                else:
                    safe_options.append(r_id)
            
            if current_turn > 15 and safe_options:
                safe_non_corners = [
                    r_id for r_id in safe_options
                    if len(context.map_graph.get(r_id, [1, 2, 3, 4])) > 3
                ]
                if safe_non_corners:
                    safe_options = safe_non_corners

            pending_options = []
            for r_id in connections:
                if (r_id in context.active_deathzones) or (r_id in settings.SHARED_ACTIVE_DEATHZONES):
                    pass
                else:
                    pending_options.append(r_id)
            
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
                    thought=f"Tactical retreat: Outnumbered on this tile ({allies_here} vs {len(threats_here)}). Escaping immediately to: {target_name}"
                )

        # PRIORITY 2: GUNAKAN OBAT DARURAT (HP < 50 ATAU END-GAME HP PUSH)
        if hp < 50 or (current_turn >= 58 and hp < 100):
            for item in inventory:
                if isinstance(item, dict):
                    item_name = item.get("name") or item.get("displayName") or ""
                    item_id = item.get("id", "")
                    if item_name in ["Medkit", "Emergency Food", "Bandage"] and item_id:
                        context.last_action_type = "use_item"
                        thought_msg = f"Emergency Healing: HP is critical ({hp}/100). Consuming {item_name} before moving."
                        if current_turn >= 58:
                            thought_msg = f"End-game push (Turn {current_turn}). Maximizing HP ({hp}/100) with {item_name} for tie-breaker."
                        return UtilityBehavior.build_use_item_action(
                            item_id=item_id,
                            thought=thought_msg
                        )

        # PRIORITY 3: MELARIKAN DIRI DARI ANCAMAN JARAK DEKAT (HP < 60 DAN THREATS HERE)
        if hp < 60 and threats_here:
            if region_id and region_id not in settings.SOS_TARGETS:
                settings.SOS_TARGETS.append(region_id)

            connections = current_region.get("connections", [])
            
            safe_options = []
            for r_id in connections:
                if (r_id in context.pending_deathzones) or (r_id in context.active_deathzones) or (r_id in settings.SHARED_ACTIVE_DEATHZONES):
                    rejected_name = context.region_names.get(r_id, f"Hex-{r_id[:8]}")
                    logger.warning(f"[Deadzone Filter] [{bot_name}] Rejecting escape connection (threat): {rejected_name} (Hex-{r_id[:8]}) - DANGEROUS/DEADZONE!")
                else:
                    safe_options.append(r_id)
            
            if current_turn > 15 and safe_options:
                safe_non_corners = [
                    r_id for r_id in safe_options
                    if len(context.map_graph.get(r_id, [1, 2, 3, 4])) > 3
                ]
                if safe_non_corners:
                    safe_options = safe_non_corners

            pending_options = []
            for r_id in connections:
                if (r_id in context.active_deathzones) or (r_id in settings.SHARED_ACTIVE_DEATHZONES):
                    pass
                else:
                    pending_options.append(r_id)
            
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
                    thought=f"HP is compromised ({hp}/100). Escaping close-range threats to safe region: {target_name}"
                )

        # PRIORITY 4: RECOVERY ENERGI DARURAT (EP < 2)
        if ep < 2:
            for item in inventory:
                if isinstance(item, dict):
                    item_name = item.get("name") or item.get("displayName") or ""
                    item_id = item.get("id", "")
                    if item_name in ["Energy drink", "Medkit"] and item_id:
                        context.last_action_type = "use_item"
                        return UtilityBehavior.build_use_item_action(
                            item_id=item_id,
                            thought=f"Energy critical ({ep}/10) in safe zone. Consuming {item_name} to recover EP."
                        )

        # PRIORITY 5: INTERAKSI DENGAN MEDICAL FACILITY (HP < 70)
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
                                thought="HP is moderately low. Interacting with Medical Facility to heal."
                            )

        # PRIORITY 6: MELARIKAN DIRI DARI ZONA KEMATIAN TERTUNDA (PENDING ZONE)
        in_danger_zone = (region_id in context.pending_deathzones)
        if in_danger_zone or (hp < 40 and threats_here):
            if threats_here and region_id and region_id not in settings.SOS_TARGETS:
                settings.SOS_TARGETS.append(region_id)

            connections = current_region.get("connections", [])
            
            safe_options = []
            for r_id in connections:
                if (r_id in context.pending_deathzones) or (r_id in context.active_deathzones) or (r_id in settings.SHARED_ACTIVE_DEATHZONES):
                    rejected_name = context.region_names.get(r_id, f"Hex-{r_id[:8]}")
                    logger.warning(f"[Deadzone Filter] [{bot_name}] Rejecting escape connection (pending zone): {rejected_name} (Hex-{r_id[:8]}) - DANGEROUS/DEADZONE!")
                else:
                    safe_options.append(r_id)
            
            if current_turn > 15 and safe_options:
                safe_non_corners = [
                    r_id for r_id in safe_options
                    if len(context.map_graph.get(r_id, [1, 2, 3, 4])) > 3
                ]
                if safe_non_corners:
                    safe_options = safe_non_corners

            pending_options = []
            for r_id in connections:
                if (r_id in context.active_deathzones) or (r_id in settings.SHARED_ACTIVE_DEATHZONES):
                    pass
                else:
                    pending_options.append(r_id)
            
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