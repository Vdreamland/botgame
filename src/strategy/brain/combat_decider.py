import random
from typing import Dict, Any, Optional
from src.strategy.brain.game_context import GameContext
from src.strategy.brain.base_decider import BaseDecider
from src.strategy.behaviors.combat_behavior import CombatBehavior
from src.strategy.behaviors.utility_behavior import UtilityBehavior
from config.game_data import WEAPONS

class CombatDecider(BaseDecider):
    
    def decide(self, view: Dict[str, Any], context: GameContext) -> Optional[Dict[str, Any]]:
        view_self = view.get("self", {})
        self_id = view_self.get("id", "")
        hp = view_self.get("hp", 100)
        ep = view_self.get("ep", 10)
        inventory = view_self.get("inventory", [])
        
        if ep < 1:
            return None

        equipped_weapon = view_self.get("equippedWeapon")
        equipped_weapon_name = "None"
        if equipped_weapon:
            equipped_weapon_name = equipped_weapon.get("name") if isinstance(equipped_weapon, dict) else str(equipped_weapon)

        # Hanya masukkan senjata yang sanggup kita bayar biaya EP-nya saat ini
        weapons_we_have = []
        
        eq_cost = WEAPONS.get(equipped_weapon_name, {}).get("ep_cost", 1) if equipped_weapon_name in WEAPONS else 1
        if ep >= eq_cost:
            weapons_we_have.append(equipped_weapon_name)
        else:
            # Jika EP tidak cukup untuk senjata terpasang, default ke Fist (Tinju) jika EP >= 1
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

        opponents = []
        for p in context.opponents_data.get("players", []):
            opponents.append({"id": p["id"], "name": p["name"], "hp": p["hp"], "region_id": p["region_id"], "is_monster": False})
            
        for m in context.opponents_data.get("monsters", []):
            opponents.append({"id": m["id"], "name": m["name"], "hp": m["hp"], "region_id": m["region_id"], "is_monster": True})

        current_region = view.get("currentRegion", {})
        current_region_id = current_region.get("id")
        connections = current_region.get("connections", [])

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

            if distance <= max_available_range:
                opp["distance"] = distance
                valid_targets.append(opp)

        if not valid_targets:
            return None

        valid_targets.sort(key=lambda x: (x["is_monster"], x["hp"]))
        best_target = valid_targets[0]
        
        # ALGORITMA PENYARINGAN CERDAS GUARDIAN (Smart Guardian Finisher)
        if "Guardian" in best_target["name"] and best_target["hp"] > 15:
            alternative_target = None
            for t in valid_targets:
                if "Guardian" not in t["name"] or t["hp"] <= 15:
                    alternative_target = t
                    break
            
            if alternative_target:
                best_target = alternative_target
            else:
                return None

        target_id = best_target["id"]
        target_name = best_target["name"]
        target_distance = best_target["distance"]

        context.last_attack_region = best_target["region_id"]

        # Logika Penyelamatan: Jika senjata aktif saat ini tidak terjangkau oleh sisa EP
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
            # Jika tidak ada alternatif senjata terjangkau di tas, serahkan giliran ke decider lain
            return None

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