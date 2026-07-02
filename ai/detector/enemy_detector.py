import collections
from config.agen_config import get_configured_bots
from game_data.monster_info import MONSTERS, GUARDIAN_STATS

def get_ally_names() -> set:
    try:
        bots = get_configured_bots()
        return {b["name"] for b in bots if "name" in b}
    except Exception:
        return set()

def classify_agent(agent_name: str, self_bot_name: str) -> str:
    if not isinstance(agent_name, str):
        return "player"
    if agent_name == self_bot_name:
        return "self"
    if agent_name.startswith("Guardian"):
        return "guardian"
    allies = get_ally_names()
    if agent_name in allies:
        return "ally"
    return "player"

def calculate_region_layers(view: dict) -> dict:
    layers = {}
    if not isinstance(view, dict):
        return layers
    current_region = view.get("currentRegion", {})
    if not isinstance(current_region, dict):
        return layers
    start_id = current_region.get("id")
    if not start_id:
        return layers
    regions = view.get("regions", {})
    queue = collections.deque([(start_id, 0)])
    visited = {start_id}
    while queue:
        region_id, dist = queue.popleft()
        layers[region_id] = dist
        connections = []
        if region_id == start_id:
            connections = current_region.get("connections", [])
        else:
            region_data = regions.get(region_id, {}) if isinstance(regions, dict) else {}
            if isinstance(region_data, dict):
                connections = region_data.get("connections", [])
        if isinstance(connections, list):
            for conn in connections:
                if conn not in visited:
                    if isinstance(regions, dict) and conn in regions:
                        visited.add(conn)
                        queue.append((conn, dist + 1))
                    elif conn in connections:
                        visited.add(conn)
                        queue.append((conn, dist + 1))
    return layers

def get_visible_enemies_by_layer(view: dict, self_bot_name: str) -> dict:
    layers = calculate_region_layers(view)
    max_layer = max(layers.values()) if layers else 0
    layer_summary = {}
    for i in range(max_layer + 1):
        layer_summary[i] = {"P": 0, "M": 0, "A": 0}
    agents = view.get("visibleAgents", [])
    if isinstance(agents, list):
        for agent in agents:
            if isinstance(agent, dict):
                is_alive = bool(agent.get("isAlive", agent.get("is_alive", True)))
                hp = agent.get("hp", 100)
                if not is_alive or hp == 0:
                    continue
                name = agent.get("name")
                classification = classify_agent(name, self_bot_name)
                if classification == "self":
                    continue
                region_id = agent.get("regionId") or agent.get("region")
                layer = layers.get(region_id)
                if layer is not None:
                    if classification == "ally":
                        layer_summary[layer]["A"] += 1
                    elif classification == "guardian":
                        layer_summary[layer]["M"] += 1
                    else:
                        layer_summary[layer]["P"] += 1
    monsters = view.get("visibleMonsters", [])
    if isinstance(monsters, list):
        for monster in monsters:
            if isinstance(monster, dict):
                hp = monster.get("hp", 25)
                if hp == 0:
                    continue
                region_id = monster.get("regionId") or monster.get("region")
                layer = layers.get(region_id)
                if layer is not None:
                    layer_summary[layer]["M"] += 1
    return layer_summary

def get_detailed_enemy_stats(view: dict, self_bot_name: str) -> dict:
    layers = calculate_region_layers(view)
    detailed = {
        "players": [],
        "allies": [],
        "monsters": []
    }
    if not isinstance(view, dict):
        return detailed
    agents = view.get("visibleAgents", [])
    if isinstance(agents, list):
        for agent in agents:
            if isinstance(agent, dict):
                is_alive = bool(agent.get("isAlive", agent.get("is_alive", True)))
                hp = agent.get("hp", 100)
                if not is_alive or hp == 0:
                    continue
                name = agent.get("name")
                classification = classify_agent(name, self_bot_name)
                if classification == "self":
                    continue
                region_id = agent.get("regionId") or agent.get("region")
                layer = layers.get(region_id, -1)
                eq_weapon = agent.get("equippedWeapon")
                weapon_name = eq_weapon.get("name", "None") if isinstance(eq_weapon, dict) else "None"
                eq_armour = agent.get("equippedArmor")
                armour_name = eq_armour.get("name", "None") if isinstance(eq_armour, dict) else "None"
                agent_stats = {
                    "name": name,
                    "hp": hp,
                    "ep": agent.get("ep", 10),
                    "atk": agent.get("atk", 25),
                    "def": agent.get("def", 5),
                    "weapon": weapon_name,
                    "armour": armour_name,
                    "layer": layer,
                    "region_id": region_id
                }
                if classification == "ally":
                    detailed["allies"].append(agent_stats)
                elif classification == "guardian":
                    monster_stats = {
                        "type": "Guardian",
                        "hp": agent.get("hp", 150),
                        "atk": agent.get("atk", 20),
                        "def": agent.get("def", 34),
                        "is_guardian": True,
                        "layer": layer,
                        "region_id": region_id
                    }
                    detailed["monsters"].append(monster_stats)
                else:
                    detailed["players"].append(agent_stats)
    monsters = view.get("visibleMonsters", [])
    if isinstance(monsters, list):
        for monster in monsters:
            if isinstance(monster, dict):
                hp = monster.get("hp", 25)
                if hp == 0:
                    continue
                m_type = monster.get("type", "Unknown")
                is_g = monster.get("is_guardian", monster.get("isGuardian", False))
                region_id = monster.get("regionId") or monster.get("region")
                layer = layers.get(region_id, -1)
                if is_g or m_type == "Guardian":
                    hp = monster.get("hp", GUARDIAN_STATS.get("hp", 150))
                    atk = GUARDIAN_STATS.get("atk", 20)
                    defense = GUARDIAN_STATS.get("def", 34)
                    is_g = True
                else:
                    spec = MONSTERS.get(m_type, {})
                    hp = monster.get("hp", spec.get("hp", 25))
                    atk = spec.get("atk", 15)
                    defense = spec.get("def", 1)
                monster_stats = {
                    "type": m_type,
                    "hp": hp,
                    "atk": atk,
                    "def": defense,
                    "is_guardian": is_g,
                    "layer": layer,
                    "region_id": region_id
                }
                detailed["monsters"].append(monster_stats)
    return detailed