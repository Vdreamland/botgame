# ui/loot_logs.py

from utility.detector.inventory_detector import detect_agent_inventory

def detect_loot_log_string(self_data: dict) -> str:
    """Mengurai statistik penimbunan koin sMoltz serta sisa slot penyimpanan inventaris tas bot"""
    inv = detect_agent_inventory(self_data)
    inventory_str = inv["items_str"]
    slot_count = inv["slot_count"]
    
    loot_text = f"Inventory ({slot_count}/10 Slots) : {inventory_str}"
    return loot_text