from typing import Dict, Any, Optional
from config.game_data import WEAPONS
from config import settings
from src.strategy.evaluators.threat_evaluator import ThreatEvaluator

class StateParser:
    
    @staticmethod
    def parse(view: Dict[str, Any], context: Any, computed_action: Optional[Dict[str, Any]], is_new_turn: bool) -> Dict[str, Any]:
        view_self = view.get("self", {})
        bot_name = view_self.get("name", "")
        
        hp = view_self.get("hp", 100)
        max_hp = view_self.get("maxHp", 100)
        ep = view_self.get("ep", 10)
        max_ep = view_self.get("maxEp", 10)
        def_val = view_self.get("def", 5)
        kills = view_self.get("kills", 0)
        server_is_alive = view_self.get("isAlive", True)
        alert_gauge = view_self.get("alertGauge", 0)
        alert_active = view_self.get("alertActive", False)

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
        region_id = current_region.get("id")
        
        z_id_short = region_id[:8] if region_id else "unknown"
        location_now = f"{current_region.get('name', 'Unknown')} (Hex-{z_id_short})"

        # PARSE GROUND DATA (Items + Interactable Facilities)
        ground_entries = []
        
        # A. Cek Barang (Items)
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
        
        for name, qty in ground_counts.items():
            ground_entries.append(f"{name} x{qty}")

        # B. Cek Fasilitas (Interactables)
        interactables = current_region.get("interactables", [])
        for fac in interactables:
            if isinstance(fac, dict):
                f_name = fac.get("name", "Unknown Facility")
                f_used = fac.get("isUsed", False)
                if not f_used:
                    ground_entries.append(f"[{f_name}]")

        if not ground_entries:
            ground_str = "None"
        else:
            ground_str = " / ".join(ground_entries)

        location_planning = "None"
        if computed_action:
            action_data = computed_action.get("data", {})
            action_type = action_data.get("type")
            if action_type == "move":
                target_id = action_data.get("regionId", "")
                planned_name = context.region_names.get(target_id, "Hex")
                location_planning = f"{planned_name} (Hex-{target_id[:8]})"
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
            elif action_type == "explore":
                location_planning = "EXPLORING RUIN"

        is_deathzone = current_region.get("isDeathZone", False)
        pending_zones = context.pending_deathzones
        
        if is_deathzone:
            deadzone_status = "ACTIVE"
        elif pending_zones:
            deadzone_status = "INCOMING"
        else:
            deadzone_status = "SAFE"

        if pending_zones:
            pending_names = []
            for z_id in pending_zones:
                z_name = context.region_names.get(z_id, f"Hex-{z_id[:8]}")
                pending_names.append(f"{z_name} (Hex-{z_id[:8]})")
            deadzone_warning = " / ".join(pending_names)
        else:
            deadzone_warning = "None"

        layer0, layer1, layer2 = ThreatEvaluator.scan_enemies(view, view_self.get("id", ""))

        raw_pack = settings.BOT_ACTIVE_PACKS.get(bot_name, "None")
        pack_names = {
            "0": "Moltz Expert (CAT-00)", "CAT-00": "Moltz Expert (CAT-00)",
            "1": "Item Expert (CAT-01)", "CAT-01": "Item Expert (CAT-01)",
            "2": "Goliath (CAT-02)", "CAT-02": "Goliath (CAT-02)",
            "3": "Thorns (CAT-03)", "CAT-03": "Thorns (CAT-03)",
            "4": "Scout (CAT-04)", "CAT-04": "Scout (CAT-04)",
            "5": "Ruin Expert (CAT-05)", "CAT-05": "Ruin Expert (CAT-05)",
            "6": "Berserker (CAT-06)", "CAT-06": "Berserker (CAT-06)",
            "7": "Double Attack (CAT-07)", "CAT-07": "Double Attack (CAT-07)",
            "8": "Heart of the Giant (CAT-08)", "CAT-08": "Heart of the Giant (CAT-08)",
            "9": "Bomber (CAT-09)", "CAT-09": "Bomber (CAT-09)",
            "10": "Trail Ward (CAT-10)", "CAT-10": "Trail Ward (CAT-10)",
            "11": "Ranged (CAT-11)", "CAT-11": "Ranged (CAT-11)",
            "12": "Sword Master (CAT-12)", "CAT-12": "Sword Master (CAT-12)",
            "13": "Duelist (CAT-13)", "CAT-13": "Duelist (CAT-13)",
            "14": "Raider (CAT-14)", "CAT-14": "Raider (CAT-14)",
            "15": "Last Stand (CAT-15)", "CAT-15": "Last Stand (CAT-15)",
            "16": "Iron Heart (CAT-16)", "CAT-16": "Iron Heart (CAT-16)",
            "17": "Sunflame Cloak (CAT-17)", "CAT-17": "Sunflame Cloak (CAT-17)",
            "18": "Assassin (CAT-18)", "CAT-18": "Assassin (CAT-18)",
            "19": "Pickpocket (CAT-19)", "CAT-19": "Pickpocket (CAT-19)"
        }
        active_pack = pack_names.get(str(raw_pack), f"Unknown ({raw_pack})")
        
        weather = view.get("weather") or current_region.get("weather") or "clear"
        
        target_hp_info = ""
        if computed_action and computed_action.get("data", {}).get("type") == "attack":
            t_id = computed_action["data"].get("targetId", "")
            opps = context.opponents_data.get("players", []) + context.opponents_data.get("monsters", [])
            for o in opps:
                if o.get("id") == t_id:
                    target_hp_info = f" (Target HP: {o.get('hp', 0)})"
                    break

        recent_raw = view.get("recentMessages", [])
        recent_messages = []
        for msg in recent_raw:
            if isinstance(msg, dict):
                text = msg.get("text") or msg.get("message") or str(msg)
            else:
                text = str(msg)
            recent_messages.append(text)

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
            "layer2": layer2,
            "active_pack": active_pack,
            "weather": weather,
            "target_hp_info": target_hp_info,
            "alert_gauge": alert_gauge,
            "alert_active": alert_active,
            "recent_messages": recent_messages[-5:]
        }