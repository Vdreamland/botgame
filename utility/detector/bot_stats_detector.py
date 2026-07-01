# utility/detector/bot_stats_detector.py

from game_data.player_info import PLAYER_DEFAULT_STATS

def detect_bot_stats(self_data: dict) -> dict:
    hp = self_data.get("hp", PLAYER_DEFAULT_STATS["hp"])
    max_hp = self_data.get("maxHp") or self_data.get("max_hp") or PLAYER_DEFAULT_STATS["hp"]
    ep = self_data.get("ep", PLAYER_DEFAULT_STATS["max_ep"])
    max_ep = self_data.get("maxEp") or self_data.get("max_ep") or PLAYER_DEFAULT_STATS["max_ep"]
    kills = self_data.get("kills") or 0
    atk = self_data.get("atk") or PLAYER_DEFAULT_STATS["atk"]
    def_val = self_data.get("def") or PLAYER_DEFAULT_STATS["def"]
    is_alive = self_data.get("isAlive", True)

    if hp <= 0:
        is_alive = False

    equipped_weapon = self_data.get("equippedWeapon")
    weapon_name = "None"
    if isinstance(equipped_weapon, dict):
        weapon_name = equipped_weapon.get("displayName") or equipped_weapon.get("name") or "None"
    elif isinstance(equipped_weapon, str):
        weapon_name = equipped_weapon

    equipped_armor = self_data.get("equippedArmor")
    armor_name = "None"
    if isinstance(equipped_armor, dict):
        armor_name = equipped_armor.get("displayName") or equipped_armor.get("name") or "None"
    elif isinstance(equipped_armor, str):
        armor_name = equipped_armor

    return {
        "hp": hp,
        "max_hp": max_hp,
        "ep": ep,
        "max_ep": max_ep,
        "kills": kills,
        "atk": atk,
        "def": def_val,
        "is_alive": is_alive,
        "weapon_name": weapon_name,
        "armor_name": armor_name
    }