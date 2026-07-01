# utility/strategy/movement_solver.py

from utility.detector.layer_detector import calculate_distances
from game_data.world_info import TERRAINS

def evaluate_movement_routes(bot_name: str, self_data: dict, current_region: dict, view_data: dict, joined_bots: list, log_state: dict) -> dict:
    """Mengevaluasi wilayah tetangga sekitar dan menghitung skor daya tarik arah gerak teraman menghindari Death Zone"""
    
    connections = current_region.get("connections") or []
    if not connections:
        return {
            "move_desire": 0.0,
            "best_region_id": None,
            "best_region_name": "None",
            "safe_directions": [],
            "all_evaluated_regions": []
        }

    our_hp = self_data.get("hp", 100)
    
    # 1. Pindai zona mati aktif & ancaman pelebaran Dead Zone mendatang
    active_death_zones = []
    if current_region.get("isDeathZone") or current_region.get("is_death_zone"):
        active_death_zones.append(current_region.get("id"))
        
    regions_list = view_data.get("visibleRegions") or view_data.get("regions") or []
    for r in regions_list:
        if isinstance(r, dict):
            if r.get("isDeathZone") or r.get("is_death_zone"):
                active_death_zones.append(r.get("id"))

    pending_dz_list = [pz.get("id") for pz in view_data.get("pendingDeathzones", []) if isinstance(pz, dict)]
    
    # 2. Ambil peta jarak BFS untuk mendeteksi posisi layer unit sekitar
    distances = calculate_distances(current_region, view_data)

    evaluated_routes = []
    
    # 3. Hitung skor daya tarik untuk setiap jalur koneksi wilayah tetangga
    for target_id in connections:
        # Cari detail nama dan tipe terrain wilayah tetangga ini
        target_name = target_id[:8]
        target_terrain = "plains"
        is_target_dz = target_id in active_death_zones
        
        for r in regions_list:
            if isinstance(r, dict) and r.get("id") == target_id:
                target_name = r.get("name") or target_name
                target_terrain = r.get("terrain") or target_terrain
                break
                
        # Skor awal berdasarkan Terrain statis dari world_info
        terrain_key = target_terrain.lower().strip()
        terrain_stats = TERRAINS.get(terrain_key, TERRAINS["plains"])
        move_ep_extra = terrain_stats.get("move_ep_extra", 0)
        
        # Base Attraction Score
        score = 50
        
        # Penalti energi gerakan: Kurangi daya tarik jika bergerak memakan biaya EP besar (badai/water)
        score -= (move_ep_extra * 25)

        # PROTEKSI MUTLAK: Berikan penalti penolakan ekstrim jika wilayah tersebut adalah Death Zone aktif atau mendatang
        if is_target_dz:
            score -= 1000  # Penolakan zona mati aktif
        if target_id in pending_dz_list:
            score -= 800   # Penolakan zona mati mendatang

        # Taktis: Berikan magnet ketertarikan rute jika wilayah tersebut tercatat di memori titik pembunuhan terbaru
        recent_kills = log_state.get("recent_kill_zones") or []
        if target_id in recent_kills:
            score += 45    # Tarik bot ke arah penjarahan koin sMoltz jatuh

        # Taktis: Deteksi jika ada musuh sekarat di wilayah tersebut yang layak dikejar
        visible_agents = view_data.get("visibleAgents") or []
        for agent in visible_agents:
            if isinstance(agent, dict):
                a_name = agent.get("name")
                if a_name == bot_name:
                    continue
                is_alive = agent.get("isAlive") or agent.get("is_alive", True)
                if is_alive:
                    enemy_r_id = agent.get("regionId") or agent.get("region_id")
                    if enemy_r_id == target_id:
                        enemy_hp = agent.get("hp", 100)
                        if enemy_hp < 40 and our_hp >= 50:
                            score += 35  # Tarik untuk melakukan pengejaran (Chase)
                        elif enemy_hp >= 70 and our_hp < 40:
                            score -= 30  # Hindari wilayah jika di sana ada musuh sehat sedangkan kita sekarat

        # Taktis: Cegah bot melakukan gerakan bolak-balik tanpa tujuan (Ping-pong Movement)
        move_history = log_state.get("visited_regions") or []
        if move_history and move_history[-1] == target_id:
            score -= 20  # Kurangi prioritas wilayah yang baru saja kita tinggalkan

        evaluated_routes.append({
            "region_id": target_id,
            "region_name": target_name,
            "score": score,
            "is_safe": score > -500
        })

    # Urutkan rute dari skor daya tarik tertinggi ke terendah
    evaluated_routes.sort(key=lambda x: x["score"], reverse=True)
    
    best_route = evaluated_routes[0] if evaluated_routes else None
    
    # Hitung skor keinginan bergerak final
    move_desire = 0.0
    best_region_id = None
    best_region_name = "None"
    
    if best_route and best_route["is_safe"]:
        best_region_id = best_route["region_id"]
        best_region_name = best_route["region_name"]
        
        # Jika berada di zona mati, hasrat bergerak harus dipaksa maksimal (100) untuk evakuasi
        if current_region.get("id") in active_death_zones or current_region.get("id") in pending_dz_list:
            move_desire = 100.0
        else:
            move_desire = min(100.0, max(0.0, best_route["score"]))

    safe_directions = [r["region_id"] for r in evaluated_routes if r["is_safe"]]

    return {
        "move_desire": move_desire,
        "best_region_id": best_region_id,
        "best_region_name": best_region_name,
        "safe_directions": safe_directions,
        "all_evaluated_regions": evaluated_routes
    }