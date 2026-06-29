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

        # 1. Mengalkulasi jangkauan maksimal senjata yang kita miliki saat ini
        weapons_we_have = [equipped_weapon_name]
        for item in inventory:
            if isinstance(item, dict):
                item_name = item.get("name") or item.get("displayName") or ""
                if item_name in WEAPONS:
                    weapons_we_have.append(item_name)
            else:
                item_name = str(item)
                if item_name in WEAPONS:
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

        # 2. Memindai seluruh musuh hidup yang berada di dalam jangkauan jangkau tembak kita
        # Kita memprioritaskan Pemain lain (untuk ranking Kills) dibanding Monster
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

        # Menyortir target: Prioritaskan Pemain lain terlebih dahulu, kemudian cari yang HP-nya terkecil (sekarat)
        valid_targets.sort(key=lambda x: (x["is_monster"], x["hp"]))
        best_target = valid_targets[0]
        target_id = best_target["id"]
        target_name = best_target["name"]
        target_distance = best_target["distance"]

        # 3. Eksekusi Taktik Tukar Senjata Dinamis (Dynamic Weapon Swapping) berdasarkan Jarak Layer
        if target_distance == 0:
            # Target berada di Layer 0 (Dekat). Kita ingin memakai Katana (Melee terkuat)
            if "Katana" in weapons_we_have and equipped_weapon_name != "Katana":
                # Cari ID Katana di dalam tas untuk dipasang gratis
                for item in inventory:
                    name = item.get("name") or item.get("displayName") or "" if isinstance(item, dict) else str(item)
                    i_id = item.get("id") or name if isinstance(item, dict) else str(item)
                    if name == "Katana":
                        context.last_action_type = "equip"
                        return UtilityBehavior.build_equip_action(
                            item_id=i_id,
                            thought=f"Target {target_name} is in Layer 0. Swapping to Katana for maximum DPS."
                        )
            # Jika Katana sudah terpasang (atau tidak punya Katana), langsung hantam!
            context.last_action_type = "attack"
            return CombatBehavior.build_attack_action(
                target_id=target_id,
                thought=f"Attacking {target_name} in Layer 0 with {equipped_weapon_name}."
            )

        elif target_distance >= 1:
            # Target berada di Layer 1 atau 2 (Jauh). Kita wajib menggunakan Sniper Rifle atau Bow/Pistol
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
            # Jika Senjata Ranged sudah terpasang, langsung tembak!
            context.last_action_type = "attack"
            return CombatBehavior.build_attack_action(
                target_id=target_id,
                thought=f"Sniping {target_name} in Layer {target_distance} with {equipped_weapon_name}."
            )

        return None