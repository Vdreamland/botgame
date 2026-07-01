# utility/strategy/decision_engine.py

from utility.strategy.combat_solver import evaluate_combat_targets
from utility.strategy.loot_solver import evaluate_loot_desire
from utility.strategy.movement_solver import evaluate_movement_routes

def make_decision(bot_name: str, self_data: dict, current_region: dict, view_data: dict, joined_bots: list, log_state: dict) -> dict:
    """Otak Utama (Desire Scorer) yang menimbang hasrat taktis dan merangkai urutan eksekusi tindakan turn terbaik"""
    
    # 1. Eksekusi Pengecekan dari Seluruh Berkas Pemecah Taktis Terpisah (Code Reuse)
    combat_res = evaluate_combat_targets(bot_name, self_data, current_region, view_data, joined_bots)
    loot_res = evaluate_loot_desire(bot_name, self_data, current_region, view_data, joined_bots, log_state)
    move_res = evaluate_movement_routes(bot_name, self_data, current_region, view_data, joined_bots, log_state)

    our_hp = self_data.get("hp", 100)
    our_ep = self_data.get("ep", 10)
    
    # 2. Hitung Hasrat Pemulihan Darah (Heal Desire)
    heal_desire = 0.0
    best_heal_item_id = None
    
    # Periksa ketersediaan item pemulihan di dalam inventaris secara dinamis
    inventory = self_data.get("inventory") or []
    heal_items = []
    for item in inventory:
        if isinstance(item, dict):
            i_id = item.get("id") or item.get("instanceId")
            i_name = (item.get("displayName") or item.get("name") or "").lower()
            if "medkit" in i_name or "bandage" in i_name or "food" in i_name:
                heal_items.append((i_id, i_name))
                
    if heal_items and our_hp < 75:
        # Urutkan: Prioritaskan item penyembuh terbaik jika HP sangat kritis
        heal_items.sort(key=lambda x: "medkit" in x[1], reverse=True)
        best_heal_item_id = heal_items[0][0]
        
        # Skor keinginan memulihkan darah berbanding lurus dengan ketipisan HP
        heal_desire = (75 - our_hp) * 1.3
        heal_desire = min(100.0, heal_desire)

    # 3. Hitung Hasrat Istirahat (Rest Desire)
    rest_desire = 0.0
    if our_ep < 3:
        # Jika tidak ada ancaman musuh instan, hasrat istirahat bertambah besar
        threat_penalty = 50 if combat_res["can_attack"] else 0
        rest_desire = max(0.0, (10 - our_ep) * 10 - threat_penalty)

    # 4. Kumpulkan & Bandingkan Semua Skor Keinginan Tindakan (Utility Scoring)
    attack_score = combat_res["best_target"]["priority_score"] / 15 if combat_res["can_attack"] and combat_res["best_target"] else 0.0
    attack_score = min(100.0, max(0.0, attack_score))
    
    loot_score = loot_res["loot_desire"]
    move_score = move_res["move_desire"]
    
    desires = [
        ("attack", attack_score),
        ("heal", heal_desire),
        ("loot", loot_score),
        ("move", move_score),
        ("rest", rest_desire)
    ]
    
    # Pilih keinginan taktis yang memiliki skor tertinggi
    desires.sort(key=lambda x: x[1], reverse=True)
    chosen_strategy = desires[0][0]
    
    # 5. Rangkai Aksi Payload Final & Integrasikan Otomasi "Loot & Run" (Pickup Gratis)
    action_data = None
    thought_string = f"Taktis: Memilih strategi '{chosen_strategy}' dengan bobot evaluasi tertinggi."

    # Otomasi Penjarahan Gratis: Jika ada koin sMoltz/item layak ambil di lantai kaki kita, sapu bersih dahulu
    free_pickups = []
    if loot_res["items_to_pickup"]:
        # Ambil maksimal 3 item gratis per turn agar tidak menyepam jaringan
        free_pickups = loot_res["items_to_pickup"][:3]

    if chosen_strategy == "attack" and combat_res["best_target"]:
        target_id = combat_res["best_target"].get("name")
        action_data = {
            "type": "attack",
            "targetId": target_id
        }
        thought_string = f"Menyerang musuh '{target_id}' karena peluang menang sangat besar."
        
    elif chosen_strategy == "heal" and best_heal_item_id:
        action_data = {
            "type": "use_item",
            "itemId": best_heal_item_id
        }
        thought_string = f"Melakukan pemulihan menggunakan item penyembuh karena HP kritis ({our_hp})."
        
    elif chosen_strategy == "loot" and free_pickups:
        # Jika strategi utama adalah menjarah koin, ambil item pertama sebagai aksi utama (jika free_pickups gagal disisipkan)
        action_data = {
            "type": "pickup",
            "itemId": free_pickups[0]
        }
        thought_string = "Fokus menyapu bersih koin sMoltz dan barang berharga di lantai."
        
    elif chosen_strategy == "move" and move_res["best_region_id"]:
        dest_id = move_res["best_region_id"]
        dest_name = move_res["best_region_name"]
        action_data = {
            "type": "move",
            "regionId": dest_id
        }
        thought_string = f"Mengatur navigasi rute bergerak menuju '{dest_name}' demi keamanan taktis."
        
        # Catat memori wilayah jangka pendek untuk mencegah gerakan ping-pong berulang
        if "visited_regions" not in log_state:
            log_state["visited_regions"] = []
        log_state["visited_regions"].append(dest_id)
        if len(log_state["visited_regions"]) > 10:
            log_state["visited_regions"].pop(0)
            
    elif chosen_strategy == "rest":
        action_data = {
            "type": "rest"
        }
        thought_string = f"Melakukan istirahat sejenak untuk memulihkan energi EP (EP: {our_ep})."
        
    else:
        # Fallback jika tidak ada opsi yang aman: Cari rute gerak terbaik yang tersedia
        if move_res["best_region_id"]:
            action_data = {
                "type": "move",
                "regionId": move_res["best_region_id"]
            }
            thought_string = "Melakukan manuver pergerakan darurat demi keselamatan."
        else:
            action_data = {
                "type": "rest"
            }
            thought_string = "Semua rute terblokir atau tidak aman. Berdiam diri menimbun energi."

    return {
        "action": action_data,
        "free_pickups": free_pickups,
        "thought": thought_string
    }