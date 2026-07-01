# ui/zone_logs.py

from utility.detector.zone_detector import detect_zone

def detect_zone_log_string(current_region: dict, view_data: dict) -> str:
    """Mengurai kondisi medan, cuaca, jangkauan penglihatan (visi), serta zona bahaya secara terperinci"""
    zone = detect_zone(current_region, view_data)
    region_name = zone["region_name"]
    terrain = zone["terrain"]
    weather = zone["weather"]
    links_count = zone["links_count"]
    vision = zone["vision"]

    # Deteksi jumlah total wilayah terlihat di radar
    regions_list = view_data.get("visibleRegions") or view_data.get("regions")
    if isinstance(regions_list, list):
        visibility_zones = len(regions_list)
    else:
        visibility_zones = links_count + 1

    # Deteksi peringatan zona bahaya Dead Zone mendatang (Incoming)
    pending_dz = view_data.get("pendingDeathzones") or []
    if pending_dz:
        names = [rz.get("name") or rz.get("id") or "Unknown" for rz in pending_dz if isinstance(rz, dict)]
        dz_warning = f"Incoming ({', '.join(names)})"
    else:
        dz_warning = "None"

    # Deteksi daftar koordinat wilayah yang sudah berubah aktif menjadi zona mati
    active_dz_names = []
    if current_region.get("isDeathZone") or current_region.get("is_death_zone"):
        curr_name = current_region.get("name") or "Current Region"
        active_dz_names.append(current_region.get("id"))

    regions_to_check = view_data.get("visibleRegions") or view_data.get("regions") or []
    for rz in regions_to_check:
        if isinstance(rz, dict):
            if rz.get("isDeathZone") or rz.get("is_death_zone"):
                name = rz.get("name") or rz.get("id")
                if name and rz.get("id") not in active_dz_names:
                    active_dz_names.append(rz.get("id"))

    active_dz = ", ".join(active_dz_names) if active_dz_names else "None"

    zone_text = (
        f"Visibility [{visibility_zones}]\n"
        f"Location : {region_name} / Terrain : {terrain} / Weather : {weather} / Vision {vision} / Links {links_count}\n"
        f"DeadZoneWarning : {dz_warning}\n"
        f"Active DeathZones : {active_dz}"
    )
    return zone_text