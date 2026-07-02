def format_agent_status_log(bot_name: str, turn: int, view_data: dict) -> str:
    if not view_data:
        return f"# Turn {turn} [{bot_name}]\nHP: Unknown | EP: Unknown | Atk: Unknown | Def: Unknown | Kills: Unknown |\nEquipped : Weapon : None | Armour : None\nInventory 0/10 : Empty"

    self_data = view_data.get("self", {})
    hp = self_data.get("hp", "Unknown")
    ep = self_data.get("ep", "Unknown")
    atk = self_data.get("atk", "Unknown")
    defense = self_data.get("def", "Unknown")
    kills = self_data.get("kills", "Unknown")

    weapon = self_data.get("equippedWeapon")
    weapon_name = "None"
    if weapon:
        if isinstance(weapon, dict):
            weapon_name = weapon.get("name") or weapon.get("itemKey") or "Unknown"
        else:
            weapon_name = str(weapon)

    armour = self_data.get("equippedArmour") or self_data.get("armour")
    armour_name = "None"
    if armour:
        if isinstance(armour, dict):
            armour_name = armour.get("name") or armour.get("itemKey") or "Unknown"
        else:
            armour_name = str(armour)

    inventory = self_data.get("inventory", [])
    if not isinstance(inventory, list):
        inventory = []

    inv_slots_used = len(inventory)
    
    item_counts = {}
    for item in inventory:
        if isinstance(item, dict):
            name = item.get("name") or item.get("itemKey") or "Unknown"
            qty = item.get("quantity") or item.get("qty") or 1
            item_counts[name] = item_counts.get(name, 0) + qty
        else:
            name = str(item)
            item_counts[name] = item_counts.get(name, 0) + 1

    inv_items = [f"{name} [{total_qty}]" for name, total_qty in item_counts.items()]
    inv_display = ", ".join(inv_items) if inv_items else "Empty"

    return (
        f"# Turn {turn} [{bot_name}]\n"
        f"HP: {hp} | EP: {ep} | Atk: {atk} | Def: {defense} | Kills: {kills} |\n"
        f"Equipped : Weapon : {weapon_name} | Armour : {armour_name}\n"
        f"Inventory {inv_slots_used}/10 : {inv_display}"
    )