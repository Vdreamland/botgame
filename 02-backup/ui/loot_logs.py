# ui/loot_logs.py

from utility.detector.inventory_detector import detect_inventory

def detect_loot_log_string(self_data: dict, current_region: dict) -> str:
    """Mengurai statistik tas bot serta data koin, barang, dan fasilitas interaktif di lantai"""
    inv = detect_inventory(self_data)
    inventory_str = inv["items_str"]
    slot_count = inv["slot_count"]
    
    # Ekstrak koin sMoltz dan barang berharga di lantai kaki bot secara dinamis
    ground_items = current_region.get("items") or current_region.get("groundItems") or []
    item_names = []
    for item in ground_items:
        if isinstance(item, dict):
            qty = item.get("quantity") or item.get("qty")
            name = item.get("displayName") or item.get("name") or "Unknown"
            if qty and qty > 1:
                item_names.append(f"{qty} {name}")
            else:
                item_names.append(name)
        else:
            item_names.append(str(item))
    ground_items_str = ", ".join(item_names) if item_names else "None"
    
    # Ekstrak kondisi fasilitas interaktif di tile saat ini (Unused / Used)
    interactables = current_region.get("interactables") or current_region.get("facilities") or []
    fac_names = []
    for f in interactables:
        if isinstance(f, dict):
            f_type = f.get("type") or f.get("id") or "Facility"
            f_used = "Used" if f.get("isUsed") or f.get("is_used") else "Unused"
            fac_names.append(f"{f_type.replace('_', ' ').title()} ({f_used})")
    facilities_str = ", ".join(fac_names) if fac_names else "None"
    
    loot_text = (
        f"Inventory ({slot_count}/10 Slots) : {inventory_str}\n"
        f"GroundLoot : Items: [{ground_items_str}] | Facilities: [{facilities_str}]"
    )
    return loot_text