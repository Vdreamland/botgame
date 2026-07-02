def detect_ground_loot(view: dict) -> list:
    loot_list = []
    if not isinstance(view, dict):
        return loot_list
    current_region = view.get("currentRegion", {})
    if not isinstance(current_region, dict):
        return loot_list
    items = current_region.get("items", [])
    if isinstance(items, list):
        counts = {}
        for item in items:
            if isinstance(item, dict):
                name = item.get("name")
                if name:
                    counts[name] = counts.get(name, 0) + 1
            elif isinstance(item, str):
                counts[item] = counts.get(item, 0) + 1
        for name, count in counts.items():
            loot_list.append(f"{name} [{count}]")
    facility = current_region.get("facility")
    if facility:
        is_used = current_region.get("facilityUsed", current_region.get("isUsed", False))
        if not is_used:
            loot_list.append(facility)
    interactables = current_region.get("interactables", [])
    if isinstance(interactables, list):
        for item in interactables:
            if isinstance(item, dict):
                name = item.get("name")
                is_used = item.get("used", item.get("isUsed", False))
                if name and not is_used:
                    if name not in loot_list and f"{name} [1]" not in loot_list:
                        loot_list.append(name)
    return loot_list

def has_loot_on_ground(view: dict) -> bool:
    return len(detect_ground_loot(view)) > 0