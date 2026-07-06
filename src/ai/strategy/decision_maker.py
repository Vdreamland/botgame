from src.ai.strategy.priority.equipped_priority import EquippedPriority
from src.ai.strategy.priority.ground_loot_priority import GroundLootPriority
from src.ai.strategy.priority.interact_priority import InteractPriority
from src.ai.strategy.priority.recovery_priority import RecoveryPriority
from src.ai.strategy.priority.target_kill_priority import TargetKillPriority
from src.ai.strategy.priority.survival_priority import SurvivalPriority
from src.ai.strategy.navigation_strategy import NavigationStrategy
from src.ai.strategy.ruin_exploration_strategy import RuinExplorationStrategy

from src.utils.action_helper import (
    create_move_action,
    create_attack_action,
    create_loot_action,
    create_explore_action,
    create_use_item_action,
    create_equip_action,
    create_rest_action,
    create_discard_action
)

class DecisionMaker:
    def __init__(self):
        self.priorities = [
            EquippedPriority(),
            GroundLootPriority(),
            InteractPriority(),
            RecoveryPriority(),
            TargetKillPriority(),
            NavigationStrategy(),
            RuinExplorationStrategy(),
            SurvivalPriority()
        ]
        self.last_decision = {
            "action": "NONE",
            "score": 0,
            "target": "None"
        }

    def make_decision(self, manager, raw_data):
        view = raw_data.get("view", {})
        self_data = view.get("self", {})
        my_id = self_data.get("id")
        hp = self_data.get("hp", 100)
        current_region = view.get("currentRegion", {})
        current_region_id = current_region.get("id")
        
        in_deadzone = current_region.get("isDeathZone", False)
        
        has_layer_0_enemies = False
        for agent in view.get("visibleAgents", []):
            if agent.get("id") != my_id and agent.get("regionId") == current_region_id and agent.get("isAlive", True):
                has_layer_0_enemies = True
                break
        if not has_layer_0_enemies:
            for monster in view.get("visibleMonsters", []):
                if monster.get("regionId") == current_region_id and monster.get("isAlive", True):
                    has_layer_0_enemies = True
                    break
                    
        is_emergency = in_deadzone or (hp < 30 and has_layer_0_enemies)
        
        best_score = -1
        best_action = None
        
        for priority in self.priorities:
            score, action = priority.evaluate(manager, raw_data)
            if not action:
                continue
                
            action_type = action.get("action_type")
            
            if in_deadzone:
                if action_type not in ["move", "flee"]:
                    score = 0
            elif is_emergency:
                if action_type in ["loot", "interact", "explore", "rest", "discard"]:
                    score = 0
            elif has_layer_0_enemies:
                if action_type in ["explore", "rest", "interact"]:
                    score = 0
                elif action_type in ["loot", "discard"]:
                    if score < 80:
                        score = 0
                        
            if score > best_score:
                best_score = score
                best_action = action
        
        if not best_action:
            self.last_decision = {"action": "EXPLORE", "score": 22, "target": "None"}
            return create_explore_action()
            
        action_type = best_action.get("action_type")
        target_name = "None"
        
        if action_type == "equip":
            target_name = best_action.get("item_id")
        elif action_type == "loot":
            target_name = best_action.get("item_id")
        elif action_type == "use_item":
            target_name = best_action.get("item_id")
        elif action_type == "attack":
            target_name = best_action.get("target_id")
        elif action_type == "move":
            target_name = best_action.get("destination")
        elif action_type == "interact":
            target_name = best_action.get("facility_name", "Facility")
        elif action_type == "discard":
            target_name = best_action.get("item_name", "Item")
            
        self.last_decision = {
            "action": action_type.upper(),
            "score": best_score,
            "target": target_name
        }
        
        if action_type == "equip":
            return create_equip_action(best_action["item_id"])
        elif action_type == "loot":
            return create_loot_action(best_action["item_id"])
        elif action_type == "use_item":
            return create_use_item_action(best_action["item_id"])
        elif action_type == "attack":
            target_region_id = best_action.get("target_region_id")
            current_region_id = raw_data.get("view", {}).get("currentRegion", {}).get("id")
            if target_region_id and current_region_id and target_region_id != current_region_id:
                if hasattr(manager, "pending_loot_regions"):
                    if target_region_id not in manager.pending_loot_regions:
                        manager.pending_loot_regions.append(target_region_id)
            return create_attack_action(best_action["target_id"], best_action["target_type"])
        elif action_type == "move":
            return create_move_action(best_action["destination"])
        elif action_type == "rest":
            return create_rest_action()
        elif action_type == "explore":
            current_region_id = raw_data.get("view", {}).get("currentRegion", {}).get("id")
            if current_region_id and hasattr(manager, "searched_regions"):
                manager.searched_regions.add(current_region_id)
            return create_explore_action()
        elif action_type == "discard":
            return create_discard_action(best_action["item_id"])
        elif action_type == "flee":
            view = raw_data.get("view", {})
            current_region = view.get("currentRegion", {})
            connections = current_region.get("connections", [])
            
            if connections:
                gas_zones = view.get("pendingDeathzones", [])
                gas_ids = {g.get("id") for g in gas_zones if g.get("id")}
                
                from src.utils.zone_helper import get_adjacent_safe_zones
                safe_targets = get_adjacent_safe_zones(connections, gas_ids)
                
                visible_regions = view.get("visibleRegions", [])
                dead_ids = {r.get("id") for r in visible_regions if r.get("id") and r.get("isDeathZone")}
                
                truly_safe = [rid for rid in safe_targets if rid not in dead_ids]
                
                visible_agents = view.get("visibleAgents", [])
                visible_monsters = view.get("visibleMonsters", [])
                
                enemy_occupied_regions = set()
                for agent in visible_agents:
                    if agent.get("isAlive", True):
                        enemy_occupied_regions.add(agent.get("regionId"))
                for monster in visible_monsters:
                    if monster.get("isAlive", True):
                        enemy_occupied_regions.add(monster.get("regionId"))
                        
                perfect_safe = [rid for rid in truly_safe if rid not in enemy_occupied_regions]
                
                if perfect_safe:
                    return create_move_action(perfect_safe[0])
                elif truly_safe:
                    return create_move_action(truly_safe[0])
                elif safe_targets:
                    return create_move_action(safe_targets[0])
                else:
                    return create_move_action(connections[0])
            return create_explore_action()
        elif action_type == "interact":
            current_region_id = raw_data.get("view", {}).get("currentRegion", {}).get("id")
            facility_name = best_action.get("facility_name")
            if current_region_id and facility_name:
                facility_key = f"{current_region_id}_{facility_name}"
                if hasattr(manager, "interacted_facilities"):
                    manager.interacted_facilities.add(facility_key)
            return {
                "type": "action",
                "data": {
                    "type": "interact",
                    "facilityId": best_action["facility_id"]
                }
            }
            
        return create_explore_action()