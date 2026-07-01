# utility/strategy/loot_solver.py

from utility.detector.layer_detector import calculate_distances
from utility.detector.bot_stats_detector import detect_agent_stats
from utility.detector.inventory_detector import detect_agent_inventory

def evaluate_loot_desire(bot_name: str, self_data: dict, current_region: dict, view_data: dict, joined_bots: list, log_state: dict) -> dict:
    """Mengevaluasi nilai kelayakan penjarahan koin sMoltz atau item di tanah berdasarkan Need, Risk, dan Expected Value"""
    
    ground_items = current_region.get("items") or current_region.get("groundItems") or []
    if not ground_items:
        return {
            "loot_desire": 0.0,
            "items_to_pickup": [],
            "action_recommendation": "ignore",
            "estimated_ev": 0.0
        }

    # 1. Analisis Kapabilitas & Kebutuhan (Need Score) Bot Kita
    our_stats = detect_agent_stats(self_data)
    our_hp = our_stats["hp"]
    our_max_hp = our_stats["max_hp"]
    our_ep = our_stats["ep"]
    
    our_inv = detect_agent_inventory(self_data)
    slot_count = our_inv["slot_count"]
    is_inventory_full = slot_count >= 10

    # 2. Hitung Nilai Ancaman di Area Saat Ini (Risk Score)
    distances = calculate_distances(current_region, view_data)
    risk_score = 0
    
    # Deteksi jika ada ancaman di sekitar kita secara spasial
    visible_agents = view_data.get("visibleAgents") or []
    for agent in visible_agents:
        if isinstance(agent, dict):
            a_name = agent.get("name")
            if a_name == bot_name:
                continue
                
            is_alive = agent.get("isAlive")
            if is_alive is None:
                is_alive = agent.get("is_alive", True)
                
            if is_alive:
                r_id = agent.get("regionId") or agent.get("region_id")
                dist = distances.get(r_id)
                if dist is not None:
                    if dist == 0:
                        risk_score += 60  # Musuh di tile yang sama sangat berisiko
                    elif dist == 1:
                        risk_score += 30  # Musuh di sebelah tile kita cukup berisiko
                    elif dist == 2:
                        risk_score += 10

    visible_monsters = view_data.get("visibleMonsters") or []
    for monster in visible_monsters:
        if isinstance(monster, dict):
            is_alive = monster.get("isAlive") or monster.get("is_alive", True)
            if is_alive:
                r_id = monster.get("regionId") or monster.get("region_id")
                dist = distances.get(r_id)
                if dist is not None:
                    if dist == 0:
                        risk_score += 40  # Monster di tile yang sama
                    elif dist == 1:
                        risk_score += 20

    is_dz = current_region.get("isDeathZone") or current_region.get("is_death_zone")
    if is_dz:
        risk_score += 30  # Bahaya tambahan berada di Dead Zone

    # Batasi skor risiko di skala 0-100
    risk_score = min(100, risk_score)

    items_to_pickup = []
    total_desire_score = 0.0
    items_count = 0

    # 3. Hitung Skor Keinginan (Loot Score) untuk Setiap Item di Lantai
    for item in ground_items:
        if not isinstance(item, dict):
            continue
            
        item_id = item.get("id") or item.get("instanceId")
        item_name = (item.get("displayName") or item.get("name") or "").lower()
        
        item_type = "utility"
        if "food" in item_name or "bandage" in item_name or "medkit" in item_name or "drink" in item_name:
            item_type = "recovery"
        elif "smoltz" in item_name or "moltz" in item_name:
            item_type = "currency"
        elif "sword" in item_name or "dagger" in item_name or "katana" in item_name or "bow" in item_name or "pistol" in item_name or "sniper" in item_name:
            item_type = "weapon"
        elif "armor" in item_name or "leather" in item_name or "chainmail" in item_name:
            item_type = "armor"

        # Tentukan nilai dasar (Item Value) & Kebutuhan Bot (Need)
        item_value = 50
        need_score = 50

        if item_type == "currency":
            item_value = 100
            need_score = 100  # sMoltz koin selalu menjadi prioritas utama penjarahan
            # Koin sMoltz tidak memakan kapasitas slot inventaris
        elif is_inventory_full:
            # Jika inventaris penuh, abaikan item non-koin kecuali bernilai sangat tinggi
            item_value = 10
            need_score = 0
        else:
            if item_type == "weapon":
                has_weapon = self_data.get("equippedWeapon") is not None
                need_score = 100 if not has_weapon else 15
                item_value = 80 if "katana" in item_name or "sniper" in item_name else 40
            elif item_type == "armor":
                has_armor = self_data.get("equippedArmor") is not None
                need_score = 80 if not has_armor else 20
                item_value = 70
            elif item_type == "recovery":
                hp_ratio = our_hp / our_max_hp
                need_score = int((1.0 - hp_ratio) * 100)
                item_value = 60 if "medkit" in item_name else 30

        # Formula Expected Value (EV) untuk item ini: Success Chance vs Failure
        success_chance = (100 - risk_score) / 100.0
        failure_chance = risk_score / 100.0
        
        reward = need_score + item_value
        penalty = 80 if item_type != "currency" else 10  # Penalti lebih rendah untuk koin karena instan
        
        expected_value = (reward * success_chance) - (penalty * failure_chance)
        
        if expected_value > 20:
            items_to_pickup.append(item_id)
            total_desire_score += expected_value
            items_count += 1

    # Normalisasikan skor hasrat penjarahan total di skala 0-100
    loot_desire = min(100.0, max(0.0, total_desire_score / items_count)) if items_count > 0 else 0.0
    action_recommendation = "pickup" if items_to_pickup and loot_desire > 40 else "ignore"

    return {
        "loot_desire": loot_desire,
        "items_to_pickup": items_to_pickup,
        "action_recommendation": action_recommendation,
        "estimated_ev": total_desire_score
    }