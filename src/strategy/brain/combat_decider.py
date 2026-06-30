import random
from typing import Dict, Any, Optional
from src.strategy.brain.game_context import GameContext
from src.strategy.brain.base_decider import BaseDecider
from src.strategy.behaviors.combat_behavior import CombatBehavior
from src.strategy.behaviors.utility_behavior import UtilityBehavior
from config.game_data import WEAPONS
from config import settings

# Mengimpor modul taktis dan kalkulator pembantu
from src.strategy.brain.combat_helpers import get_weapons_and_range, estimate_hits_to_kill
from src.strategy.brain.combat_tactics import evaluate_adjacent_looting
from src.strategy.brain.utility_helpers import MELEE_WEAPONS, RANGED_WEAPONS, ARMORS

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
        
        # 1. INSTANT FREE-PICKUP GRAB (EP 0)
        # Hitung kapasitas riil
        backpack_count = sum(1 for item in inventory if (item.get("name") if isinstance(item, dict) else str(item)) != "sMoltz")
        equipped_weapon = view_self.get("equippedWeapon")
        equipped_armor = view_self.get("equippedArmor")
        total_slots = backpack_count + (1 if equipped_weapon else 0) + (1 if equipped_armor else 0)

        for g_item in ground_items:
            if isinstance(g_item, dict):
                g_name = g_item.get("name") or g_item.get("displayName") or ""
                g_id = g_item.get("id") or g_name
            else:
                g_name = str(g_item)
                g_id = g_name
                
            # A. Ambil sMoltz (Tanpa Batas Slot)
            if g_name == "sMoltz":
                context.last_action_type = "pickup"
                return UtilityBehavior.build_pickup_action(item_id=g_id, thought="Snatched sMoltz instantly.")
                
            # B. Ambil Gear/Meds jika Slot Tersedia (<10)
            if total_slots < 10:
                # Ambil Obat
                if g_name in ["Medkit", "Emergency Food", "Bandage", "Energy drink"]:
                    context.last_action_type = "pickup"
                    return UtilityBehavior.build_pickup_action(item_id=g_id, thought=f"Secured {g_name} instantly.")
                
                # Ambil Senjata/Armor Berharga (Free Action)
                if g_name in MELEE_WEAPONS or g_name in RANGED_WEAPONS or g_name in ARMORS:
                    context.last_action_type = "pickup"
                    return UtilityBehavior.build_pickup_action(item_id=g_id, thought=f"Snatching {g_name} for free gear upgrade.")

        # 2. IDENTIFIKASI SENJATA DAN JARAK
        weapons_we_have, max_available_range, equipped_weapon_name = get_weapons_and_range(view_self, ep, inventory)
        active_pack = settings.BOT_ACTIVE_PACKS.get(bot_name, "")

        # 3. BUILD LIST MUSUH
        opponents = []
        for p in context.opponents_data.get("players", []):
            if p["name"] in settings.ALLY_NAMES: continue
            opponents.append({"id": p["id"], "name": p["name"], "hp": p["hp"], "region_id": p["region_id"], "is_monster": False})
        for m in context.opponents_data.get("monsters", []):
            opponents.append({"id": m["id"], "name": m["name"], "hp": m["hp"], "region_id": m["region_id"], "is_monster": True})

        current_region_id = current_region.get("id")
        connections = current_region.get("connections", [])

        # 4. FILTER TARGET (PACK CONSTRAINTS)
        valid_targets = []
        for opp in opponents:
            opp_region_id = opp["region_id"]
            distance = 0 if opp_region_id == current_region_id else (1 if opp_region_id in connections else 2)
            if active_pack in ["CAT-11", "Ranged"] and distance == 0: continue
            if active_pack in ["CAT-12", "Sword Master"] and distance >= 1: continue
            if distance <= max_available_range:
                opp["distance"] = distance
                valid_targets.append(opp)

        if not valid_targets:
            return None

        # 5. TAKTIK MENJARAH BERSEBELAHAN (THREAT-AWARE)
        looting_action = evaluate_adjacent_looting(hp, valid_targets, connections, context)
        if looting_action: return looting_action

        # 6. PENGUNCI TARGET (TTK & DEF)
        weapon_atk_bonus = WEAPONS.get(equipped_weapon_name, {}).get("atk_bonus", 0) if equipped_weapon_name in WEAPONS else 0
        our_atk = 25 + weapon_atk_bonus

        best_target = None
        if context.last_target_id:
            for t in valid_targets:
                if t["id"] == context.last_target_id:
                    best_target = t
                    break
        if not best_target:
            valid_targets.sort(key=lambda x: (x["is_monster"], estimate_hits_to_kill(x, our_atk)))
            best_target = valid_targets[0]
            context.last_target_id = best_target["id"]

        target_id = best_target["id"]
        target_name = best_target["name"]
        target_distance = best_target["distance"]
        context.last_attack_region = best_target["region_id"]

        # 7. EP LOCKOUT & SWAP
        eq_cost = WEAPONS.get(equipped_weapon_name, {}).get("ep_cost", 1) if equipped_weapon_name in WEAPONS else 1
        if ep < eq_cost:
            affordable = [w for w in weapons_we_have if w != equipped_weapon_name and w != "Fist" and w != "None"]
            if affordable:
                affordable.sort(key=lambda w: WEAPONS.get(w, {}).get("atk_bonus", 0), reverse=True)
                for item in inventory:
                    name = item.get("name") or item.get("displayName") or "" if isinstance(item, dict) else str(item)
                    if name == affordable[0]:
                        context.last_action_type = "equip"
                        return UtilityBehavior.build_equip_action(item_id=item.get("id", name), thought=f"Swapping to {name}.")
            else:
                context.last_action_type = "rest"
                return UtilityBehavior.build_rest_action(thought="Resting for EP.")

        # 8. RESOLUSI PERTEMPURAN
        if target_distance == 0:
            if "Katana" in weapons_we_have and equipped_weapon_name != "Katana":
                for item in inventory:
                    name = item.get("name") or item.get("displayName") or ""
                    if name == "Katana":
                        context.last_action_type = "equip"
                        return UtilityBehavior.build_equip_action(item_id=item.get("id", name), thought="Equipping Katana.")
            context.last_action_type = "attack"
            return CombatBehavior.build_attack_action(target_id=target_id, thought=f"Attacking {target_name}.")
        elif target_distance >= 1:
            has_sniper_now = "Sniper rifle" in weapons_we_have
            preferred = "Sniper rifle" if has_sniper_now else ("Pistol" if "Pistol" in weapons_we_have else "Bow")
            if preferred in weapons_we_have and equipped_weapon_name != preferred:
                for item in inventory:
                    name = item.get("name") or item.get("displayName") or ""
                    if name == preferred:
                        context.last_action_type = "equip"
                        return UtilityBehavior.build_equip_action(item_id=item.get("id", name), thought=f"Swapping to {preferred}.")
            context.last_action_type = "attack"
            return CombatBehavior.build_attack_action(target_id=target_id, thought=f"Sniping {target_name}.")

        return None