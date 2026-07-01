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
    our_max_hp = self_data.get("maxHp") or self_data.get("max_hp") or 100
    our_ep = self_data.get("ep", 10)
    our_max_ep = self_data.get("maxEp") or self_data.get("max_ep") or 10
    
    # 2. Hitung Hasrat Pemulihan Darah (Heal Desire)
    heal_desire = 0.0
    best_heal_item_id = None
    
    inventory = self_data.get("inventory") or []
    heal_items = []
    
    # Saring inventaris dengan aman (mendukung format tipe data Dictionary maupun String)
    for item in inventory:
        item_id = None
        item_name = ""
        
        if isinstance(item, dict):
            item_id = item.get("id") or item.get("instanceId") or item.get("instance_id")
            item_name = (item.get("displayName") or item.get("name") or "").lower()
        elif isinstance(item, str):
            item_id = item
            item_name = item.lower()
            
        if item_id and ("medkit" in item_name or "bandage" in item_name or "food" in item_name):
            heal_items.append((item_id, item_name))
                
    if heal_items and our_hp < 75:
        heal_items.sort(key=lambda x: "medkit" in x[1], reverse=True)
        best_heal_item_id = heal_items[0][0]
        heal_desire = (75 - our_hp) * 1.3
        heal_desire = min(100.0, heal_desire)

    # 3. Hitung Hasrat Istirahat (Rest Desire)
    rest_desire = 0.0
    if our_ep < 3:
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
    
    # 5. Otomasi Pemakaian Senjata / Armor Gratis (EP 0 Auto-Equip) [3]
    free_equips = []
    
    equipped_weapon = self_data.get("equippedWeapon")
    has_weapon = isinstance(equipped_weapon, dict) or (isinstance(equipped_weapon, str) and equipped_weapon != "None")
    
    equipped_armor = self_data.get("equippedArmor")
    has_armor = isinstance(equipped_armor, dict) or (isinstance(equipped_armor, str) and equipped_armor != "None")

    # Pindai seluruh isi inventaris secara cerdas untuk dipasang instan (mendukung format Dictionary & String)
    for item in inventory:
        item_id = None
        item_name = ""
        
        if isinstance(item, dict):
            item_id = item.get("id") or item.get("instanceId") or item.get("instance_id")
            item_name = (item.get("displayName") or item.get("name") or "").lower()
        elif isinstance(item, str):
            item_id = item
            item_name = item.lower()
            
        if not item_id:
            continue
            
        # Jika tas mendeteksi ada senjata yang belum terpasang, masukkan ke daftar pasang otomatis
        if "sword" in item_name or "dagger" in item_name or "katana" in item_name or "bow" in item_name or "pistol" in item_name or "sniper" in item_name:
            if not has_weapon:
                free_equips.append(item_id)
                has_weapon = True  # Tandai agar tidak melakukan double equip dalam 1 turn
        # Jika tas mendeteksi ada armor yang belum terpasang, masukkan ke daftar pasang otomatis
        elif "armor" in item_name or "leather" in item_name or "chainmail" in item_name:
            if not has_armor:
                free_equips.append(item_id)
                has_armor = True

    # 6. Rangkai Aksi Payload Final & Integrasikan Otomasi "Loot & Run"
    action_data = None
    thought_string = f"Taktis: Memilih strategi '{chosen_strategy}' dengan bobot evaluasi tertinggi."

    free_pickups = []
    if loot_res["items_to_pickup"]:
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
        action_data = {
            "type": "pickup",
            "itemId": free_pickups[0]
        }
        thought_string = "Fokus menyapu bersih koin sMoltz dan barang berharga di lobi lantai."
        
    elif chosen_strategy == "move" and move_res["best_region_id"]:
        dest_id = move_res["best_region_id"]
        dest_name = move_res["best_region_name"]
        action_data = {
            "type": "move",
            "regionId": dest_id
        }
        thought_string = f"Mengatur navigasi rute bergerak menuju '{dest_name}' demi keamanan taktis."
        
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
        "free_equips": free_equips,
        "thought": thought_string
    }