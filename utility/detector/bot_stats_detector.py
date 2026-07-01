# utility/detector/bot_stats_detector.py

from game_data.player_info import PLAYER_DEFAULT_STATS
from game_data.armour_info import ARMOURS

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
    armor_desc = "None"
    if isinstance(equipped_armor, dict):
        armor_name = equipped_armor.get("displayName") or equipped_armor.get("name") or "None"
        armor_grade = equipped_armor.get("grade") or "N/A"
        armor_def = equipped_armor.get("defBonus") or equipped_armor.get("def_bonus") or 0
        
        if armor_grade == "N/A" or armor_def == 0:
            for a_id, a_stats in ARMOURS.items():
                if a_id in armor_name.lower() or a_stats.get("display_name", "").lower() in armor_name.lower():
                    if armor_grade == "N/A":
                        armor_grade = a_stats.get("grade", "N/A").upper()
                    if armor_def == 0:
                        armor_def = a_stats.get("def_bonus", 0)
                    break
                    
        armor_desc = f"{armor_name} (Grade: {armor_grade}, +{armor_def} DEF)"
    elif isinstance(equipped_armor, str):
        armor_name = equipped_armor
        armor_desc = equipped_armor

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
        "armor_name": armor_name,
        "armor_desc": armor_desc
    }

def detect_agent_stats(agent_data: dict) -> dict:
    hp = agent_data.get("hp", PLAYER_DEFAULT_STATS["hp"])
    max_hp = agent_data.get("maxHp") or agent_data.get("max_hp") or PLAYER_DEFAULT_STATS["hp"]
    ep = agent_data.get("ep", PLAYER_DEFAULT_STATS["max_ep"])
    max_ep = agent_data.get("maxEp") or agent_data.get("max_ep") or PLAYER_DEFAULT_STATS["max_ep"]
    atk = agent_data.get("atk") or PLAYER_DEFAULT_STATS["atk"]
    def_val = agent_data.get("def") or PLAYER_DEFAULT_STATS["def"]
    is_alive = agent_data.get("isAlive")
    if is_alive is None:
        is_alive = agent_data.get("is_alive", True)

    if hp <= 0:
        is_alive = False

    equipped_weapon = agent_data.get("equippedWeapon")
    weapon_name = "None"
    if isinstance(equipped_weapon, dict):
        weapon_name = equipped_weapon.get("displayName") or equipped_weapon.get("name") or "None"
    elif isinstance(equipped_weapon, str):
        weapon_name = equipped_weapon

    equipped_armor = agent_data.get("equippedArmor")
    armor_name = "None"
    armor_desc = "None"
    if isinstance(equipped_armor, dict):
        armor_name = equipped_armor.get("displayName") or equipped_armor.get("name") or "None"
        armor_grade = equipped_armor.get("grade") or "N/A"
        armor_def = equipped_armor.get("defBonus") or equipped_armor.get("def_bonus") or 0
        
        if armor_grade == "N/A" or armor_def == 0:
            for a_id, a_stats in ARMOURS.items():
                if a_id in armor_name.lower() or a_stats.get("display_name", "").lower() in armor_name.lower():
                    if armor_grade == "N/A":
                        armor_grade = a_stats.get("grade", "N/A").upper()
                    if armor_def == 0:
                        armor_def = a_stats.get("def_bonus", 0)
                    break
                    
        armor_desc = f"{armor_name} (Grade: {armor_grade}, +{armor_def} DEF)"
    elif isinstance(equipped_armor, str):
        armor_name = equipped_armor
        armor_desc = equipped_armor

    return {
        "hp": hp,
        "max_hp": max_hp,
        "ep": ep,
        "max_ep": max_ep,
        "atk": atk,
        "def": def_val,
        "is_alive": is_alive,
        "weapon_name": weapon_name,
        "armor_name": armor_name,
        "armor_desc": armor_desc
    }