# ui/combat_logs.py

from utility.detector.bot_stats_detector import detect_agent_stats

def detect_combat_log_string(bot_name: str, self_data: dict, layers: list) -> str:
    """Mengurai statistik pertempuran, HP, EP, ATK, DEF, serta status layer spasial BFS bot secara terperinci"""
    stats = detect_agent_stats(self_data)
    hp = stats["hp"]
    ep = stats["ep"]
    atk = stats["atk"]
    def_val = stats["def"]
    is_alive = stats["is_alive"]
    weapon_name = stats["weapon_name"]
    armor_desc = stats["armor_desc"]

    status_display_plain = "ALIVE" if is_alive else "DEAD"
    weapon_desc = weapon_name

    layers_parts = []
    for l_data in layers:
        layers_parts.append(f"Layer {l_data['layer']} : P {l_data['P']} / M {l_data['M']} / A {l_data['A']}")
    layers_block = " | ".join(layers_parts)

    combat_text = (
        f"Status : {status_display_plain}\n"
        f"Hp {hp} / Ep {ep}\n"
        f"ATK: {atk} / DEF: {def_val}\n"
        f"Equipped : Weapon : {weapon_desc} | Armor : {armor_desc}\n"
        f"{layers_block}"
    )
    return combat_text