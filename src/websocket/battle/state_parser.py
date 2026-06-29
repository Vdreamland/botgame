from typing import Dict, Any, Optional
from config.game_data import WEAPONS
from src.strategy.evaluators.threat_evaluator import ThreatEvaluator

class StateParser:
    
    @staticmethod
    def parse(view: Dict[str, Any], context: Any, computed_action: Optional[Dict[str, Any]], is_new_turn: bool) -> Dict[str, Any]:
        view_self = view.get("self", {})
        
        hp = view_self.get("hp", 100)
        max_hp = view_self.get("maxHp", 100)
        ep = view_self.get("ep", 10)
        max_ep = view_self.get("maxEp", 10)
        def_val = view_self.get("def", 5)
        kills = view_self.get("kills", 0)
        server_is_alive = view_self.get("isAlive", True)

        equipped_weapon = view_self.get("equippedWeapon")
        weapon_name = "None"
        weapon_atk_bonus = 0
        if equipped_weapon:
            weapon_name = equipped_weapon.get("name") if isinstance(equipped_weapon, dict) else str(equipped_weapon)
            weapon_atk_bonus = WEAPONS.get(weapon_name, {}).get("atk_bonus", 0)

        atk = 25 + weapon_atk_bonus

        equipped_armor = view_self.get("equippedArmor")
        armor_name = "None"
        if equipped_armor:
            armor_name = equipped_armor.get("name") if isinstance(equipped_armor, dict) else str(equipped_armor)

        # Parse inventory and stack quantities correctly
        inventory_raw = view_self.get("inventory", [])
        inventory_counts = {}
        for item in inventory_raw:
            if isinstance(item, dict):
                name = item.get("name") or item.get("displayName") or "Unknown Item"
                qty = item.get("quantity") or item.get("count") or item.get("amount") or 1
            else:
                name = str(item)
                qty = 1
            inventory_counts[name] = inventory_counts.get(name, 0) + qty

        if not inventory_counts:
            inventory_str = "None"
        else:
            inventory_str = " / ".join(f"{name} x{qty}" for name, qty in inventory_counts.items())

        current_region = view.get("currentRegion", {})
        location_now = current_region.get("name", "Unknown Location")

        # Parse ground items and stack quantities correctly
        ground_raw = current_region.get("items", [])
        ground_counts = {}
        for g_item in ground_raw:
            if isinstance(g_item, dict):
                g_name = g_item.get("name") or g_item.get("displayName") or "Unknown Item"
                g_qty = g_item.get("quantity") or g_item.get("count") or g_item.get("amount") or 1
            else:
                g_name = str(g_item)
                g_qty = 1
            ground_counts[g_name] = ground_counts.get(g_name, 0) + g_qty

        if not ground_counts:
            ground_str = "None"
        else:
            ground_str = " / ".join(f"{g_name} x{qty}" for g_name, qty in ground_counts.items())

        location_planning = "None"
        if computed_action:
            action_data = computed_action.get("data", {})
            action_type = action_data.get("type")
            if action_type == "move":
                target_id = action_data.get("regionId", "")
                location_planning = context.region_names.get(target_id, f"Hex-{target_id[:8]}")
            elif action_type == "rest":
                location_planning = "RESTING"
            elif action_type == "use_item":
                location_planning = "HEALING"
            elif action_type == "pickup":
                location_planning = "PICKING UP ITEM"
            elif action_type == "equip":
                location_planning = "EQUIPPING WEAPON"
            elif action_type == "interact":
                location_planning = "INTERACTING"

        is_deathzone = current_region.get("isDeathZone", False)
        
        # Robust case-insensitive check for pending death zones
        pending_zones = view.get("pendingDeathzones") or view.get("pendingDeathZones") or []
        
        if is_deathzone:
            deadzone_status = "ACTIVE"
        elif pending_zones:
            deadzone_status = "INCOMING"
        else:
            deadzone_status = "SAFE"

        if pending_zones:
            pending_names = []
            for zone in pending_zones:
                z_id = zone.get("id")
                z_name = zone.get("name") or context.region_names.get(z_id, f"Hex-{z_id[:8]}")
                pending_names.append(z_name)
            deadzone_warning = " / ".join(pending_names)
        else:
            deadzone_warning = "None"

        layer0, layer1, layer2 = ThreatEvaluator.scan_enemies(view, view_self.get("id", ""))

        return {
            "server_is_alive": server_is_alive,
            "hp": hp,
            "max_hp": max_hp,
            "ep": ep,
            "max_ep": max_ep,
            "atk": atk,
            "def_val": def_val,
            "kills": kills,
            "weapon_name": weapon_name,
            "armor_name": armor_name,
            "inventory_str": inventory_str,
            "ground_str": ground_str,
            "location_now": location_now,
            "location_planning": location_planning,
            "deadzone_status": deadzone_status,
            "deadzone_warning": deadzone_warning,
            "layer0": layer0,
            "layer1": layer1,
            "layer2": layer2
        }