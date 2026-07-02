from game_data.action_info import ALERT_SYSTEM

def get_visible_ruins_status(view: dict) -> list:
    ruins_status = []
    if not isinstance(view, dict):
        return ruins_status
    ruins = view.get("visibleRuins", [])
    if isinstance(ruins, list):
        for r in ruins:
            if isinstance(r, dict):
                ruins_status.append({
                    "ruin_id": r.get("ruinId"),
                    "is_empty": bool(r.get("isEmpty", False)),
                    "gauge": r.get("gauge", 0),
                    "max_gauge": r.get("maxGauge", 3),
                    "content_type": r.get("contentType", "unknown")
                })
    return ruins_status

def evaluate_explore_safety(view: dict) -> dict:
    safety = {
        "alert_gauge": 0,
        "alert_active": False,
        "explore_charge": ALERT_SYSTEM.get("explore_charge", 2),
        "max_gauge": ALERT_SYSTEM.get("max_gauge", 10),
        "is_safe_to_explore": True,
        "next_gauge_if_explore": 2
    }
    if not isinstance(view, dict):
        return safety
    self_data = view.get("self", {})
    if isinstance(self_data, dict):
        safety["alert_gauge"] = self_data.get("alertGauge", 0)
        safety["alert_active"] = bool(self_data.get("alertActive", False))
        safety["next_gauge_if_explore"] = safety["alert_gauge"] + safety["explore_charge"]
        if safety["alert_active"]:
            safety["is_safe_to_explore"] = False
        elif safety["next_gauge_if_explore"] >= safety["max_gauge"]:
            safety["is_safe_to_explore"] = False
    return safety