from ai.Strategy.navigation_strategy import get_navigation_priorities
from ai.Strategy.ruin_exploration_strategy import get_exploration_priorities
from ai.Strategy.priority.ground_loot_priority import get_ground_loot_priorities
from ai.Strategy.priority.equipped_priority import get_equipment_priorities
from ai.Strategy.priority.recovery_priority import get_recovery_priorities
from ai.Strategy.priority.target_priority import get_target_priorities
from ai.Strategy.priority.interact_priority import get_interact_priorities
from ai.detector.dead_zone_detector import is_dead_zone

def find_target_id(view: dict, target_name: str, target_type: str, region_id: str) -> str:
    if target_type == "player":
        agents = view.get("visibleAgents", [])
        if isinstance(agents, list):
            for a in agents:
                if isinstance(a, dict) and a.get("name") == target_name:
                    return a.get("id") or a.get("agentId")
    elif target_type == "monster":
        monsters = view.get("visibleMonsters", [])
        if isinstance(monsters, list):
            for m in monsters:
                if isinstance(m, dict) and m.get("type") == target_name:
                    m_reg = m.get("regionId") or m.get("region")
                    if m_reg == region_id:
                        return m.get("id") or m.get("monsterId")
    return None

def make_decision(view: dict, self_bot_name: str) -> dict:
    if not isinstance(view, dict):
        return {"type": "rest", "name": "None", "score": 0.0, "strategy_report": "None"}
    recovery_priorities = get_recovery_priorities(view)
    equipment_priorities = get_equipment_priorities(view)
    ground_loot_priorities = get_ground_loot_priorities(view)
    target_priorities = get_target_priorities(view, self_bot_name)
    navigation_priorities = get_navigation_priorities(view, self_bot_name)
    exploration_priorities = get_exploration_priorities(view)
    interact_priorities = get_interact_priorities(view)
    current_region = view.get("currentRegion", {})
    current_is_dz = is_dead_zone(current_region)
    best_recovery = recovery_priorities[0] if recovery_priorities else {"score": 0.0}
    best_equip = equipment_priorities[0] if equipment_priorities else {"score": 0.0}
    best_loot = ground_loot_priorities[0] if ground_loot_priorities else {"score": 0.0}
    best_target = target_priorities[0] if target_priorities else {"score": 0.0}
    best_nav = navigation_priorities[0] if navigation_priorities else {"score": 0.0}
    best_explore = exploration_priorities[0] if exploration_priorities else {"score": 0.0}
    best_interact = interact_priorities[0] if interact_priorities else {"score": 0.0}
    if current_is_dz:
        best_safe_nav = None
        for nav in navigation_priorities:
            if nav.get("score", 0.0) > 0.10:
                best_safe_nav = nav
                break
        if best_safe_nav:
            best_nav = best_safe_nav
            best_nav["score"] = 1.00
            choices = [("navigation", 1.00)]
            winner_category, winner_score = "navigation", 1.00
        else:
            choices = [
                ("recovery", best_recovery.get("score", 0.0)),
                ("equip", best_equip.get("score", 0.0)),
                ("loot", best_loot.get("score", 0.0)),
                ("target", best_target.get("score", 0.0)),
                ("navigation", best_nav.get("score", 0.0)),
                ("explore", best_explore.get("score", 0.0)),
                ("interact", best_interact.get("score", 0.0))
            ]
            choices.sort(key=lambda x: x[1], reverse=True)
            winner_category, winner_score = choices[0]
    else:
        choices = [
            ("recovery", best_recovery.get("score", 0.0)),
            ("equip", best_equip.get("score", 0.0)),
            ("loot", best_loot.get("score", 0.0)),
            ("target", best_target.get("score", 0.0)),
            ("navigation", best_nav.get("score", 0.0)),
            ("explore", best_explore.get("score", 0.0)),
            ("interact", best_interact.get("score", 0.0))
        ]
        choices.sort(key=lambda x: x[1], reverse=True)
        winner_category, winner_score = choices[0]
    report_lines = []
    if best_recovery.get("score", 0.0) >= 0.15:
        report_lines.append(f"Heal: {best_recovery['name']} ({best_recovery['score']:.2f})")
    if best_equip.get("score", 0.0) >= 0.15:
        report_lines.append(f"Equip: {best_equip['name']} ({best_equip['score']:.2f})")
    if best_loot.get("score", 0.0) >= 0.15:
        report_lines.append(f"Loot: {best_loot['name']} ({best_loot['score']:.2f})")
    if best_target.get("score", 0.0) >= 0.15:
        report_lines.append(f"Attack: {best_target['name']} ({best_target['score']:.2f})")
    if best_nav.get("score", 0.0) >= 0.15:
        report_lines.append(f"Move: {best_nav['name']} ({best_nav['score']:.2f})")
    if best_explore.get("score", 0.0) >= 0.15:
        report_lines.append(f"Explore: Ruin {best_explore['ruin_id'][:6]} ({best_explore['score']:.2f})")
    if best_interact.get("score", 0.0) >= 0.15:
        report_lines.append(f"Interact: {best_interact['name']} ({best_interact['score']:.2f})")
    avoided = [n["name"] for n in navigation_priorities if n["score"] <= 0.05]
    if avoided:
        report_lines.append(f"Avoided: {', '.join(avoided)}")
    strategy_report = " | ".join(report_lines) if report_lines else "None"
    if winner_score < 0.15:
        return {"type": "rest", "name": "None", "score": winner_score, "strategy_report": strategy_report}
    if winner_category == "recovery":
        return {
            "type": "use_item",
            "itemId": best_recovery["id"],
            "name": best_recovery["name"],
            "score": winner_score,
            "strategy_report": strategy_report
        }
    elif winner_category == "equip":
        return {
            "type": "equip",
            "itemId": best_equip["id"],
            "name": best_equip["name"],
            "score": winner_score,
            "strategy_report": strategy_report
        }
    elif winner_category == "loot":
        return {
            "type": "pickup",
            "itemId": best_loot["id"],
            "name": best_loot["name"],
            "score": winner_score,
            "strategy_report": strategy_report
        }
    elif winner_category == "target":
        t_id = find_target_id(view, best_target["name"], best_target["type"], best_target["region_id"])
        if t_id:
            return {
                "type": "attack",
                "targetId": t_id,
                "name": best_target["name"],
                "score": winner_score,
                "strategy_report": strategy_report
            }
        else:
            return {"type": "rest", "name": "None", "score": winner_score, "strategy_report": strategy_report}
    elif winner_category == "navigation":
        return {
            "type": "move",
            "regionId": best_nav["id"],
            "name": best_nav["name"],
            "score": winner_score,
            "strategy_report": strategy_report
        }
    elif winner_category == "explore":
        current_region = view.get("currentRegion", {})
        curr_id = current_region.get("id") if isinstance(current_region, dict) else None
        target_ruin_id = best_explore["ruin_id"]
        if curr_id == target_ruin_id:
            ruins = view.get("visibleRuins", [])
            for r in ruins:
                if isinstance(r, dict) and r.get("ruinId") == target_ruin_id:
                    if r.get("gauge", 0) < r.get("maxGauge", 3):
                        return {
                            "type": "explore",
                            "name": "Ruin Exploration",
                            "score": winner_score,
                            "strategy_report": strategy_report
                        }
                    else:
                        return {
                            "type": "interact",
                            "target": "ruin",
                            "name": "Ruin Vault",
                            "score": winner_score,
                            "strategy_report": strategy_report
                        }
            return {
                "type": "explore",
                "name": "Ruin Exploration",
                "score": winner_score,
                "strategy_report": strategy_report
            }
        else:
            return {
                "type": "move",
                "regionId": target_ruin_id,
                "name": f"Move to Ruin {target_ruin_id}",
                "score": winner_score,
                "strategy_report": strategy_report
            }
    elif winner_category == "interact":
        return {
            "type": "interact",
            "target": best_interact["target"],
            "name": best_interact["name"],
            "score": winner_score,
            "strategy_report": strategy_report
        }
    return {"type": "rest", "name": "None", "score": winner_score, "strategy_report": strategy_report}