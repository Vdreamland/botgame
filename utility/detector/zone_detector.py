# utility/detector/zone_detector.py

from game_data.world_info import TERRAINS, WEATHER

def detect_zone(current_region: dict, view_data: dict) -> dict:
    region_name = current_region.get("name", "Unknown")
    terrain_raw = current_region.get("terrain", "plains")
    terrain = terrain_raw.capitalize()
    weather_raw = view_data.get("weather") or "clear"
    weather = weather_raw.capitalize()
    links_count = len(current_region.get("connections", []))
    
    # Deteksi eksplisit menggunakan 'is not None' untuk menghargai angka 0 sebagai nilai valid (mencegah python falsy bug)
    vision_val = current_region.get("vision")
    if vision_val is None:
        vision_val = current_region.get("visionModifier")
    if vision_val is None:
        vision_val = current_region.get("vision_modifier")
        
    # Jika server benar-benar tidak mengirimkan data vision (None), baru gunakan fallback kalkulasi prediksi statis
    if vision_val is None:
        terrain_key = terrain_raw.lower().strip()
        weather_key = weather_raw.lower().strip()
        
        t_mod = TERRAINS.get(terrain_key, {}).get("vision_modifier", 0)
        w_mod = WEATHER.get(weather_key, {}).get("vision_modifier", 0)
        vision_val = t_mod + w_mod

    sign = "+" if vision_val > 0 else ""
    vision_str = f"{sign}{vision_val}" if vision_val != 0 else "0"

    return {
        "region_name": region_name,
        "terrain": terrain,
        "weather": weather,
        "links_count": links_count,
        "vision": vision_str
    }