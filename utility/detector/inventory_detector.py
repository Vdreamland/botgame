# utility/detector/inventory_detector.py

def detect_inventory(self_data: dict) -> dict:
    inventory = self_data.get("inventory") or []
    item_names = []
    has_smoltz = False
    non_smoltz_count = 0
    
    for item in inventory:
        item_name = ""
        qty = 1
        if isinstance(item, dict):
            item_name = (item.get("displayName") or item.get("name") or "").lower()
            try:
                qty = int(item.get("count") or item.get("quantity") or item.get("qty") or 1)
            except Exception:
                qty = 1
        elif isinstance(item, str):
            item_name = item.lower()
            
        if item_name:
            if "smoltz" in item_name or "moltz" in item_name:
                has_smoltz = True
            else:
                non_smoltz_count += qty
                
            display = item.get("displayName") or item.get("name") if isinstance(item, dict) else item
            for _ in range(qty):
                item_names.append(display)
                
    slot_count = non_smoltz_count + (1 if has_smoltz else 0)
    
    from collections import Counter
    counts = Counter(item_names)
    formatted_parts = []
    for item, count in counts.items():
        formatted_parts.append(f"{item} [{count}]")
    items_str = ", ".join(formatted_parts) if formatted_parts else "Empty"
    
    return {
        "items_str": items_str,
        "slot_count": slot_count,
        "items": item_names
    }

def detect_agent_inventory(agent_data: dict) -> dict:
    inventory = agent_data.get("inventory") or []
    item_names = []
    has_smoltz = False
    non_smoltz_count = 0
    
    for item in inventory:
        item_name = ""
        qty = 1
        if isinstance(item, dict):
            item_name = (item.get("displayName") or item.get("name") or "").lower()
            try:
                qty = int(item.get("count") or item.get("quantity") or item.get("qty") or 1)
            except Exception:
                qty = 1
        elif isinstance(item, str):
            item_name = item.lower()
            
        if item_name:
            if "smoltz" in item_name or "moltz" in item_name:
                has_smoltz = True
            else:
                non_smoltz_count += qty
                
            display = item.get("displayName") or item.get("name") if isinstance(item, dict) else item
            for _ in range(qty):
                item_names.append(display)
                
    slot_count = non_smoltz_count + (1 if has_smoltz else 0)
    
    from collections import Counter
    counts = Counter(item_names)
    formatted_parts = []
    for item, count in counts.items():
        formatted_parts.append(f"{item} [{count}]")
    items_str = ", ".join(formatted_parts) if formatted_parts else "Empty"
    
    return {
        "items_str": items_str,
        "slot_count": slot_count,
        "items": item_names
    }