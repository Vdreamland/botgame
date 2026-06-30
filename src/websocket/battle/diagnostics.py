from typing import Any

def scan_keys_for_death_or_zone(d: Any, path: str = "") -> list:
    """Pemindai kunci rekursif untuk mendeteksi letak parameter deadzone/death secara dinamis."""
    results = []
    if isinstance(d, dict):
        for k, v in d.items():
            current_path = f"{path}.{k}" if path else k
            if "death" in k.lower() or "zone" in k.lower():
                results.append((current_path, v))
            results.extend(scan_keys_for_death_or_zone(v, current_path))
    elif isinstance(d, list):
        for i, item in enumerate(d):
            results.extend(scan_keys_for_death_or_zone(item, f"{path}[{i}]"))
    return results