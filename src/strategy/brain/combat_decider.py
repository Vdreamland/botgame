import random
from typing import Dict, Any, Optional
from src.strategy.brain.game_context import GameContext
from src.strategy.brain.base_decider import BaseDecider
from src.strategy.behaviors.combat_behavior import CombatBehavior
from src.strategy.behaviors.utility_behavior import UtilityBehavior
from config.game_data import WEAPONS
from config import settings

class CombatDecider(BaseDecider):
    
    def decide(self, view: Dict[str, Any], context: GameContext) -> Optional[Dict[str, Any]]:
        view_self = view.get("self", {})
        self_id = view_self.get("id", "")
        bot_name = view_self.get("name", "")
        hp = view_self.get("hp", 100)
        ep = view_self.get("ep", 10)
        inventory = view_self.get("inventory", [])
        
        current_region = view.get("currentRegion", {})
        ground_items = current_region.get("items", [])
        
        # 1. INSTANT FREE-PICKUP GRAB
        real_inv_count = sum(1 for item in inventory if (item.get("name") if isinstance(item, dict) else str(item)) != "sMoltz")
        
        for g_item in ground_items:
            if isinstance(g_item, dict):
                g_name = g_item.get("name") or g_item.get("displayName") or ""
                g_id = g_item.get("id") or g_name
            else:
                g_name = str(g_item)
                g_id = g_name
                
            if g_name == "sMoltz":
                context.last_action_type = "pickup"
                return UtilityBehavior.build_pickup_action(
                    item_id=g_id,
                    thought="Snatched sMoltz from the ground instantly before proceeding with combat."
                )
                
            if g_name in ["Medkit", "Emergency Food", "Bandage"] and real_inv_count < 10:
                context.last_action_type = "pickup"
                return UtilityBehavior.build_pickup_action(
                    item_id=g_id,
                    thought=f"Secured crucial {g_name} from the ground instantly before continuing combat."
                )

        equipped_weapon = view_self.get("equippedWeapon")
        equipped_weapon_name = "None"
        if equipped_weapon:
            equipped_weapon_name = equipped_weapon.get("name") if isinstance(equipped_weapon, dict) else str(equipped_weapon)

        # Retrieve active pack name to apply pack-specific range constraints
        active_pack = settings.BOT_ACTIVE_PACKS.get(bot_name, "")

        has_weapon_on_ground = False
        for g_item in ground_items:
            g_name = g_item.get("name") or g_item.get("displayName") or "" if isinstance(g_item, dict) else str(g_item)
            if g_name in WEAPONS:
                has_weapon_on_ground = True
                break

        if equipped_weapon_name in ["None", "Fist"] and has_weapon_on_ground:
            return None

        weapons_we_have = []
        
        eq_cost = WEAPONS.get(equipped_weapon_name, {}).get("ep_cost", 1) if equipped_weapon_name in WEAPONS else 1
        if ep >= eq_cost:
            weapons_we_have.append(equipped_weapon_name)
        else:
            if ep >= 1:
                weapons_we_have.append("Fist")

        for item in inventory:
            if isinstance(item, dict):
                item_name = item.get("name") or item.get("displayName") or ""
            else:
                item_name = str(item)

            if item_name in WEAPONS:
                cost = WEAPONS[item_name].get("ep_cost", 1)
                if ep >= cost:
                    weapons_we_have.append(item_name)

        max_available_range = 0
        has_sniper = "Sniper rifle" in weapons_we_have
        has_ranged = any(w in ["Bow", "Pistol"] for w in weapons_we_have)
        has_melee = any(w in ["Katana", "Sword", "Dagger", "Fist"] for w in weapons_we_have)

        if has_sniper:
            max_available_range = 2
        elif has_ranged:
            max_available_range = 1
        elif has_melee:
            max_available_range = 0

        # Build list of opponents in the visible area
        opponents = []
        for p in context.opponents_data.get("players", []):
            if p["name"] in settings.ALLY_NAMES:
                continue
            opponents.append({"id": p["id"], "name": p["name"], "hp": p["hp"], "region_id": p["region_id"], "is_monster": False})
            
        for m in context.opponents_data.get("monsters", []):
            opponents.append({"id": m["id"], "name": m["name"], "hp": m["hp"], "region_id": m["region_id"], "is_monster": True})

        current_region_id = current_region.get("id")
        connections = current_region.get("connections", [])

        # 2. FILTER TARGETS ACCORDING TO PACK CONSTRAINTS (CAT-11 Ranged / CAT-12 Sword Master)
        valid_targets = []
        for opp in opponents:
            opp_region_id = opp["region_id"]
            distance = -1
            if opp_region_id == current_region_id:
                distance = 0
            elif opp_region_id in connections:
                distance = 1
            else:
                distance = 2

            # CAT-11 / Ranged pack constraints: No same-region attack (no distance 0)
            if active_pack in ["CAT-11", "Ranged"] and distance == 0:
                continue

            # CAT-12 / Sword Master pack constraints: No ranged attack (no distance 1 or 2)
            if active_pack in ["CAT-12", "Sword Master"] and distance >= 1:
                continue

            if distance <= max_available_range:
                opp["distance"] = distance
                valid_targets.append(opp)

        if not valid_targets:
            return None

        # 3. TACTICAL ADJACENT LOOTING IN COMBAT
        # Jika bot sehat dan tidak ada ancaman jarak dekat (Layer 0 kosong),
        # bot akan memotong pertempuran selama 1 giliran untuk melangkah ke ubin mayat terdekat untuk menjarah koin sMoltz!
        no_enemies_here = not any(opp["distance"] == 0 for opp in valid_targets)
        if hp >= 70 and no_enemies_here and settings.SHARED_LOOT_TARGETS:
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
                    thought=f"Tactical looting: Stepping 1-hex to adjacent secured kill site: {target_name} to harvest sMoltz."
                )

        # 4. ADVANCED TARGET SORTING (Estimated Time-to-Kill / DEF Mitigation)
        weapon_atk_bonus = WEAPONS.get(equipped_weapon_name, {}).get("atk_bonus", 0) if equipped_weapon_name in WEAPONS else 0
        our_atk = 25 + weapon_atk_bonus

        def estimate_hits_to_kill(target):
            t_name = target["name"]
            t_hp = target["hp"]
            t_def = 5  # Default baseline DEF for players
            
            if target["is_monster"]:
                if "Wolf" in t_name:
                    t_def = 1
                elif "Bear" in t_name:
                    t_def = 3
                elif "Bandit" in t_name:
                    t_def = 5
                elif "Guardian" in t_name:
                    t_def = 34
                    
            damage = max(1, our_atk - t_def)
            return t_hp / damage

        # TARGET LOCKING LOGIC
        best_target = None
        if context.last_target_id:
            # Check if our locked target is still alive and remains in range
            for t in valid_targets:
                if t["id"] == context.last_target_id:
                    best_target = t
                    break
                    
        if not best_target:
            # Prioritize monsters first, then sort by estimated hits required to kill (lowest first)
            valid_targets.sort(key=lambda x: (x["is_monster"], estimate_hits_to_kill(x)))
            best_target = valid_targets[0]
            context.last_target_id = best_target["id"]
        
        if "Guardian" in best_target["name"] and best_target["hp"] > 15:
            alternative_target = None
            for t in valid_targets:
                if "Guardian" not in t["name"] or t["hp"] <= 15:
                    alternative_target = t
                    break
            
            if alternative_target:
                best_target = alternative_target
                context.last_target_id = best_target["id"]
            else:
                return None

        target_id = best_target["id"]
        target_name = best_target["name"]
        target_distance = best_target["distance"]

        context.last_attack_region = best_target["region_id"]

        # 5. EP LOCKOUT REST FALLBACK
        # If we can't afford the equipped weapon's EP cost, swap to an affordable one.
        # If we have no affordable swap option, Rest immediately instead of idling/leaving.
        if ep < eq_cost:
            affordable_in_inv = [w for w in weapons_we_have if w != equipped_weapon_name and w != "Fist" and w != "None"]
            if affordable_in_inv:
                affordable_in_inv.sort(key=lambda w: WEAPONS.get(w, {}).get("atk_bonus", 0), reverse=True)
                swap_to = affordable_in_inv[0]
                for item in inventory:
                    name = item.get("name") or item.get("displayName") or "" if isinstance(item, dict) else str(item)
                    i_id = item.get("id") or name if isinstance(item, dict) else str(item)
                    if name == swap_to:
                        context.last_action_type = "equip"
                        return UtilityBehavior.build_equip_action(
                            item_id=i_id,
                            thought=f"Current weapon {equipped_weapon_name} is too expensive ({eq_cost} EP). Swapping to affordable {swap_to}."
                        )
            else:
                context.last_action_type = "rest"
                return UtilityBehavior.build_rest_action(
                    thought=f"EP is too low ({ep}/{eq_cost}) to attack with {equipped_weapon_name}. Resting to recover EP."
                )

        if target_distance == 0:
            if "Katana" in weapons_we_have and equipped_weapon_name != "Katana":
                for item in inventory:
                    name = item.get("name") or item.get("displayName") or "" if isinstance(item, dict) else str(item)
                    i_id = item.get("id") or name if isinstance(item, dict) else str(item)
                    if name == "Katana":
                        context.last_action_type = "equip"
                        return UtilityBehavior.build_equip_action(
                            item_id=i_id,
                            thought=f"Target {target_name} is in Layer 0. Swapping to Katana for maximum DPS."
                        )
            context.last_action_type = "attack"
            return CombatBehavior.build_attack_action(
                target_id=target_id,
                thought=f"Attacking {target_name} in Layer 0 with {equipped_weapon_name}."
            )

        elif target_distance >= 1:
            preferred_ranged = "Sniper rifle" if has_sniper else ("Pistol" if "Pistol" in weapons_we_have else "Bow")
            if preferred_ranged in weapons_we_have and equipped_weapon_name != preferred_ranged:
                for item in inventory:
                    name = item.get("name") or item.get("displayName") or "" if isinstance(item, dict) else str(item)
                    i_id = item.get("id") or name if isinstance(item, dict) else str(item)
                    if name == preferred_ranged:
                        context.last_action_type = "equip"
                        return UtilityBehavior.build_equip_action(
                            item_id=i_id,
                            thought=f"Target {target_name} is in Layer {target_distance}. Swapping to {preferred_ranged}."
                        )
            context.last_action_type = "attack"
            return CombatBehavior.build_attack_action(
                target_id=target_id,
                thought=f"Sniping {target_name} in Layer {target_distance} with {equipped_weapon_name}."
            )

        return None