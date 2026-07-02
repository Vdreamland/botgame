from ai.detector.ruin_detector import get_visible_ruins_status, evaluate_explore_safety

def get_exploration_priorities(view: dict) -> list:
    priorities = []
    if not isinstance(view, dict):
        return priorities
    ruins = get_visible_ruins_status(view)
    if not ruins:
        return priorities
    safety = evaluate_explore_safety(view)
    is_safe = safety.get("is_safe_to_explore", True)
    alert_gauge = safety.get("alert_gauge", 0)
    current_region = view.get("currentRegion", {})
    curr_id = current_region.get("id") if isinstance(current_region, dict) else None
    for r in ruins:
        ruin_id = r.get("ruin_id")
        if r.get("is_empty"):
            continue
        score = 0.0
        if is_safe:
            score = 0.80
            gauge = r.get("gauge", 0)
            max_gauge = r.get("max_gauge", 3)
            progress = float(gauge) / float(max_gauge) if max_gauge > 0 else 0.0
            score += (progress * 0.15)
            if ruin_id == curr_id:
                score += 0.05
            else:
                score -= 0.10
        else:
            if alert_gauge >= 8:
                score = 0.05
            else:
                score = 0.20
        priorities.append({
            "ruin_id": ruin_id,
            "score": max(0.0, min(1.0, score))
        })
    priorities.sort(key=lambda x: x["score"], reverse=True)
    return priorities