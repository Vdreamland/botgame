# game_data/armour_info.py

# Pada versi 1.12.0, objek armor yang digunakan oleh agen dapat dipantau langsung pada 'equippedArmor'
# struktur datanya adalah: {"id": "...", "name": "...", "grade": "...", "defBonus": ...}

ARMOUR_GRADES = {
    "Common": {
        "estimated_def_bonus": 5,
        "color_code": "gray"
    },
    "Rare": {
        "estimated_def_bonus": 10,
        "color_code": "blue"
    },
    "Epic": {
        "estimated_def_bonus": 20,
        "color_code": "purple"
    },
    "Legendary": {
        "estimated_def_bonus": 35,
        "color_code": "orange"
    }
}

def get_armour_spec(grade_name, fallback_def=0):
    """
    Mengembalikan data spesifikasi pertahanan armor berdasarkan grade.
    """
    return ARMOUR_GRADES.get(grade_name, {
        "estimated_def_bonus": fallback_def,
        "color_code": "unknown"
    })