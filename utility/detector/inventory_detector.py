# utility/detector/inventory_detector.py

from collections import Counter

def detect_inventory(self_data: dict) -> dict:
    inventory = self_data.get("inventory", [])
    item_names = []
    for item in inventory:
        if isinstance(item, dict):
            name = item.get("displayName") or item.get("name") or "Unknown"
        else:
            name = str(item)
        item_names.append(name)

    counter = Counter(item_names)
    inv_parts = []
    for name, count in counter.items():
        if count > 1:
            inv_parts.append(f"{name} [{count}]")
        else:
            inv_parts.append(name)
    
    inventory_str = ", ".join(inv_parts) if inv_parts else "No items in inventory"
    return {
        "items_str": inventory_str,
        "slot_count": len(inventory)
    }