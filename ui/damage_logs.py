# ui/damage_logs.py

from game_data.weapon_info import WEAPONS
from utility.detector.layer_detector import calculate_distances
from utility.detector.bot_stats_detector import detect_agent_stats

def track_damage_event(bot_name: str, event_data: dict, log_state: dict):
    """Merekam event pertempuran/damage yang masuk ke bot ini ke dalam state"""
    event_type = event_data.get("type")
    if event_type in ("combat", "attack", "damage"):
        target = event_data.get("target") or event_data.get("targetName") or event_data.get("defender")
        attacker = event_data.get("attacker") or event_data.get("attackerName") or event_data.get("source")
        r_id = event_data.get("regionId") or event_data.get("region_id")
        
        if target == bot_name and attacker:
            if "turn_damage_events" not in log_state:
                log_state["turn_damage_events"] = []
            log_state["turn_damage_events"].append({
                "attacker": attacker,
                "region_id": r_id
            })

def get_turn_damage_reason(bot_name: str, hp: int, max_hp: int, current_region: dict, view_data: dict, joined_bots: list, log_state: dict) -> str:
    """Kalkulasi selisih HP dan simpan riwayat penyebab damage/healing per turn secara dinamis"""
    last_hp = log_state.get("last_hp")
    log_state["last_hp"] = hp  # Update untuk pembandingan turn berikutnya
    
    if last_hp is None:
        return "No damage events recorded."
        
    if hp == last_hp:
        # Bersihkan event turn ini agar tidak menumpuk ke turn berikutnya
        log_state["turn_damage_events"] = []
        return "No damage events recorded."
        
    # Kasus A: HP Berkurang (Kena Damage)
    if hp < last_hp:
        lost_hp = last_hp - hp
        
        # Pindai pesan riwayat pesan lobi (recentMessages) untuk menangkap log serangan terstruktur jika ada
        recent_messages = view_data.get("recentMessages") or []
        for msg in recent_messages:
            if isinstance(msg, str) and bot_name.lower() in msg.lower():
                if "attacked" in msg.lower() or "damaged" in msg.lower():
                    # Ekstrak nama penyerang dari pola "Attacker attacked Defender..."
                    parts = msg.split(" attacked ")
                    if len(parts) > 1:
                        attacker_candidate = parts[0].strip()
                        if "turn_damage_events" not in log_state:
                            log_state["turn_damage_events"] = []
                        # Tambahkan ke daftar kejadian jika belum tercatat
                        if not any(e["attacker"] == attacker_candidate for e in log_state["turn_damage_events"]):
                            log_state["turn_damage_events"].append({
                                "attacker": attacker_candidate,
                                "region_id": None
                            })

        events = log_state.get("turn_damage_events") or []
        log_state["turn_damage_events"] = []  # Reset untuk turn berikutnya
        
        # Jika ada catatan penyerangan pada turn ini
        if events:
            last_event = events[-1]
            attacker = last_event["attacker"]
            attacker_r_id = last_event.get("region_id")
            
            # Hitung jarak lapisan (BFS) penyerang terpusat (Code Reuse)
            attacker_layer_str = "Unknown Layer"
            distances = calculate_distances(current_region, view_data)
            
            if attacker_r_id and attacker_r_id in distances:
                layer_dist = distances[attacker_r_id]
                attacker_layer_str = f"Layer {layer_dist} (Same Region)" if layer_dist == 0 else f"Layer {layer_dist} (Ranged)"
            else:
                # Cari di visibleAgents secara dinamis menggunakan detektor umum terpusat (Code Reuse)
                for agent in (view_data.get("visibleAgents") or []):
                    if isinstance(agent, dict) and agent.get("name") == attacker:
                        t_stats = detect_agent_stats(agent)
                        r_id = agent.get("regionId") or agent.get("region_id")
                        if r_id in distances:
                            layer_dist = distances[r_id]
                            attacker_layer_str = f"Layer {layer_dist} (Same Region)" if layer_dist == 0 else f"Layer {layer_dist} (Ranged)"
                            break
                # Cari di visibleMonsters secara dinamis
                if "Unknown" in attacker_layer_str:
                    for monster in (view_data.get("visibleMonsters") or []):
                        if isinstance(monster, dict):
                            m_name = monster.get("name") or monster.get("displayName") or ""
                            if attacker.lower() in m_name.lower() or m_name.lower() in attacker.lower():
                                r_id = monster.get("regionId") or monster.get("region_id")
                                if r_id in distances:
                                    layer_dist = distances[r_id]
                                    attacker_layer_str = f"Layer {layer_dist} (Same Region)" if layer_dist == 0 else f"Layer {layer_dist} (Ranged)"
                                    break

            # Klasifikasikan jenis penyerang
            is_player = False
            for j_bot in joined_bots:
                if j_bot.lower() in attacker.lower() or attacker.lower() in j_bot.lower():
                    is_player = True
                    break
                    
            attacker_type = "Player" if is_player else "Monster"
            return f"Took {lost_hp} damage from {attacker_type}: {attacker} from {attacker_layer_str}."
            
        # Jika tidak ada penyerang tetapi berada di wilayah Dead Zone
        is_dz = current_region.get("isDeathZone") or current_region.get("is_death_zone")
        if is_dz:
            return f"Took {lost_hp} damage from DeadZone."
            
        return f"Took {lost_hp} damage from Unknown Source."

    # Kasus B: HP Bertambah (Heal/Recovery)
    if hp > last_hp:
        gained_hp = hp - last_hp
        log_state["turn_damage_events"] = []
        return f"Restored {gained_hp} HP."
        
    return "No damage events recorded."