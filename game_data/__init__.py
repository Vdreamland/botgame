# game_data/__init__.py

from .player_info import BASE_STATS, INVENTORY_LIMIT
from .monster_info import MONSTERS, GUARDIAN_STATS
from .weapon_info import WEAPONS
from .armour_info import ARMOUR_GRADES, get_armour_spec
from .item_info import RECOVERY_ITEMS, UTILITY_ITEMS, CURRENCY_ITEMS
from .action_info import ACTIONS, ALERT_SYSTEM, MAX_CHAT_LENGTH
from .relic_info import RELIC_SLOTS, RELIC_AFFIXES
from .pack_info import PACK_CATEGORIES
from .world_info import TERRAINS, WEATHERS, FACILITIES, DEATH_ZONE, TIME_SYSTEM

__all__ = [
    "BASE_STATS",
    "INVENTORY_LIMIT",
    "MONSTERS",
    "GUARDIAN_STATS",
    "WEAPONS",
    "ARMOUR_GRADES",
    "get_armour_spec",
    "RECOVERY_ITEMS",
    "UTILITY_ITEMS",
    "CURRENCY_ITEMS",
    "ACTIONS",
    "ALERT_SYSTEM",
    "MAX_CHAT_LENGTH",
    "RELIC_SLOTS",
    "RELIC_AFFIXES",
    "PACK_CATEGORIES",
    "TERRAINS",
    "WEATHERS",
    "FACILITIES",
    "DEATH_ZONE",
    "TIME_SYSTEM"
]